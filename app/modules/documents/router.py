"""
AZALS MODULE - Documents (GED) - Router
========================================

API REST pour la Gestion Electronique de Documents.
"""
from __future__ import annotations


import logging
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User, UserRole


def require_admin_role(current_user: User) -> None:
    """Vérifie que l'utilisateur a un rôle admin (DIRIGEANT ou ADMIN)."""
    role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Rôle ADMIN ou DIRIGEANT requis."
        )

from .exceptions import (
    DocumentException,
    DocumentLockedError,
    DocumentNotFoundError,
    FolderNotFoundError,
    PermissionDeniedError,
    ShareExpiredError,
    ShareInvalidPasswordError,
    StorageQuotaExceededError,
)
from .ged_service import GEDService, get_ged_service
from .models import DocumentStatus, FileCategory, LinkEntityType, RetentionPolicy
from .schemas import (
    AuditList,
    AuditResponse,
    BatchDeleteRequest,
    BatchMoveRequest,
    BatchOperationResult,
    BatchTagRequest,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CommentCreate,
    CommentResponse,
    DocumentLinkCreate,
    DocumentLinkResponse,
    DocumentList,
    DocumentResponse,
    DocumentSummary,
    DocumentUpdate,
    FolderCreate,
    FolderResponse,
    FolderTree,
    FolderUpdate,
    SearchQuery,
    SearchResponse,
    ShareCreate,
    ShareLinkAccess,
    ShareResponse,
    ShareUpdate,
    StorageStats,
    TagCreate,
    TagResponse,
    UploadResponse,
    VersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents - GED"])


def get_service(db: Session, current_user: User) -> GEDService:
    """Factory pour le service GED."""
    return get_ged_service(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        user_email=current_user.email
    )


def handle_exception(e: Exception):
    """Convertit les exceptions en HTTPException."""
    if isinstance(e, DocumentNotFoundError):
        raise HTTPException(status_code=404, detail=e.message)
    elif isinstance(e, FolderNotFoundError):
        raise HTTPException(status_code=404, detail=e.message)
    elif isinstance(e, DocumentLockedError):
        raise HTTPException(status_code=423, detail=e.message)
    elif isinstance(e, StorageQuotaExceededError):
        raise HTTPException(status_code=507, detail=e.message)
    elif isinstance(e, PermissionDeniedError):
        raise HTTPException(status_code=403, detail=e.message)
    elif isinstance(e, ShareExpiredError):
        raise HTTPException(status_code=410, detail=e.message)
    elif isinstance(e, ShareInvalidPasswordError):
        raise HTTPException(status_code=401, detail=e.message)
    elif isinstance(e, DocumentException):
        raise HTTPException(status_code=400, detail=e.message)
    else:
        logger.error(f"Erreur inattendue: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")


# =============================================================================
# ENDPOINTS DOSSIERS
# =============================================================================

@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un nouveau dossier."""
    service = get_service(db, current_user)
    try:
        return service.create_folder(data, current_user.id)
    except Exception as e:
        handle_exception(e)


@router.get("/folders", response_model=List[FolderResponse])
async def list_folders(
    parent_id: Optional[UUID] = Query(None, description="ID du dossier parent"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les dossiers."""
    service = get_service(db, current_user)
    return service.list_folders(parent_id)


@router.get("/folders/tree", response_model=List[FolderTree])
async def get_folder_tree(
    root_id: Optional[UUID] = Query(None, description="ID du dossier racine"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir l'arbre des dossiers."""
    service = get_service(db, current_user)
    return service.get_folder_tree(root_id)


@router.get("/folders/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un dossier."""
    service = get_service(db, current_user)
    folder = service.get_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Dossier non trouve")
    return folder


@router.put("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un dossier."""
    service = get_service(db, current_user)
    try:
        folder = service.update_folder(folder_id, data, current_user.id)
        if not folder:
            raise HTTPException(status_code=404, detail="Dossier non trouve")
        return folder
    except Exception as e:
        handle_exception(e)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    force: bool = Query(False, description="Forcer la suppression meme si non vide"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un dossier."""
    service = get_service(db, current_user)
    try:
        if not service.delete_folder(folder_id, force=force, user_id=current_user.id):
            raise HTTPException(status_code=404, detail="Dossier non trouve")
    except Exception as e:
        handle_exception(e)


@router.post("/folders/{folder_id}/move", response_model=FolderResponse)
async def move_folder(
    folder_id: UUID,
    target_folder_id: Optional[UUID] = Query(None, description="Dossier de destination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deplacer un dossier."""
    service = get_service(db, current_user)
    try:
        return service.move_folder(folder_id, target_folder_id, current_user.id)
    except Exception as e:
        handle_exception(e)


# =============================================================================
# ENDPOINTS DOCUMENTS - UPLOAD
# =============================================================================

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[UUID] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[FileCategory] = Form(None),
    tags: Optional[str] = Form(None),  # Tags separes par virgule
    retention_policy: RetentionPolicy = Form(RetentionPolicy.NONE),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uploader un nouveau document."""
    service = get_service(db, current_user)

    try:
        content = await file.read()
        tags_list = [t.strip() for t in tags.split(",")] if tags else []

        return service.upload_document(
            file_content=content,
            filename=file.filename,
            folder_id=folder_id,
            title=title,
            description=description,
            category=category,
            tags=tags_list,
            retention_policy=retention_policy,
            user_id=current_user.id
        )
    except Exception as e:
        handle_exception(e)


@router.post("/{document_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def upload_new_version(
    document_id: UUID,
    file: UploadFile = File(...),
    change_summary: Optional[str] = Form(None),
    change_type: str = Form("MINOR"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uploader une nouvelle version d'un document."""
    service = get_service(db, current_user)

    try:
        content = await file.read()
        return service.upload_new_version(
            document_id=document_id,
            file_content=content,
            change_summary=change_summary,
            change_type=change_type,
            user_id=current_user.id
        )
    except Exception as e:
        handle_exception(e)


# =============================================================================
# ENDPOINTS DOCUMENTS - CRUD
# =============================================================================

@router.get("", response_model=DocumentList)
async def list_documents(
    folder_id: Optional[UUID] = Query(None, description="ID du dossier"),
    include_subfolders: bool = Query(False, description="Inclure les sous-dossiers"),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    category: Optional[FileCategory] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les documents."""
    service = get_service(db, current_user)
    items, total = service.list_documents(
        folder_id=folder_id,
        include_subfolders=include_subfolders,
        status=status_filter,
        category=category,
        page=page,
        page_size=page_size
    )

    # Convertir en DocumentSummary
    summaries = [DocumentSummary.model_validate(d) for d in items]
    pages = (total + page_size - 1) // page_size

    return DocumentList(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un document."""
    service = get_service(db, current_user)
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouve")
    return document


@router.get("/code/{code}", response_model=DocumentResponse)
async def get_document_by_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un document par son code."""
    service = get_service(db, current_user)
    document = service.get_document_by_code(code)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouve")
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un document."""
    service = get_service(db, current_user)
    try:
        document = service.update_document(document_id, data, current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouve")
        return document
    except Exception as e:
        handle_exception(e)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    permanent: bool = Query(False, description="Suppression permanente"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un document."""
    service = get_service(db, current_user)
    try:
        if not service.delete_document(document_id, permanent=permanent, user_id=current_user.id):
            raise HTTPException(status_code=404, detail="Document non trouve")
    except Exception as e:
        handle_exception(e)


@router.post("/{document_id}/restore", response_model=DocumentResponse)
async def restore_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restaurer un document supprime."""
    service = get_service(db, current_user)
    document = service.restore_document(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouve")
    return document


# =============================================================================
# ENDPOINTS TELECHARGEMENT
# =============================================================================

@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    version: Optional[int] = Query(None, description="Numero de version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Telecharger un document."""
    service = get_service(db, current_user)
    try:
        content, filename, mime_type = service.download_document(
            document_id, version, current_user.id
        )

        return StreamingResponse(
            iter([content]),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content))
            }
        )
    except Exception as e:
        handle_exception(e)


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Previsualiser un document (pour les types supportes)."""
    service = get_service(db, current_user)
    try:
        content, filename, mime_type = service.download_document(
            document_id, user_id=current_user.id
        )

        # Pour les PDFs et images, afficher inline
        disposition = "inline" if mime_type in [
            "application/pdf",
            "image/png", "image/jpeg", "image/gif", "image/webp"
        ] else "attachment"

        return StreamingResponse(
            iter([content]),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'{disposition}; filename="{filename}"'
            }
        )
    except Exception as e:
        handle_exception(e)


# =============================================================================
# ENDPOINTS VERSIONS
# =============================================================================

@router.get("/{document_id}/versions", response_model=List[VersionResponse])
async def get_versions(
    document_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les versions d'un document."""
    service = get_service(db, current_user)
    versions, _ = service.get_versions(document_id, page, page_size)
    return versions


@router.post("/{document_id}/versions/{version_number}/restore", response_model=DocumentResponse)
async def restore_version(
    document_id: UUID,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restaurer une ancienne version."""
    service = get_service(db, current_user)
    try:
        return service.restore_version(document_id, version_number, current_user.id)
    except Exception as e:
        handle_exception(e)


# =============================================================================
# ENDPOINTS VERROUILLAGE
# =============================================================================

@router.post("/{document_id}/lock", response_model=DocumentResponse)
async def lock_document(
    document_id: UUID,
    reason: Optional[str] = Query(None, description="Raison du verrouillage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verrouiller un document."""
    service = get_service(db, current_user)
    try:
        return service.lock_document(document_id, reason, current_user.id)
    except Exception as e:
        handle_exception(e)


@router.post("/{document_id}/unlock", response_model=DocumentResponse)
async def unlock_document(
    document_id: UUID,
    force: bool = Query(False, description="Forcer le deverrouillage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deverrouiller un document."""
    service = get_service(db, current_user)
    try:
        return service.unlock_document(document_id, force, current_user.id)
    except Exception as e:
        handle_exception(e)


# =============================================================================
# ENDPOINTS PARTAGE
# =============================================================================

@router.post("/{document_id}/shares", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def create_share(
    document_id: UUID,
    data: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un partage."""
    service = get_service(db, current_user)
    try:
        return service.create_share(document_id, data, current_user.id)
    except Exception as e:
        handle_exception(e)


@router.get("/shares/{share_link}")
async def access_shared_document(
    share_link: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Acceder a un document partage via lien."""
    # Note: Pas besoin d'authentification pour les liens publics
    service = GEDService(db, "public")  # Tenant special pour partages
    try:
        share, document = service.get_share_by_link(share_link, password)
        return {
            "share": share,
            "document": document
        }
    except Exception as e:
        handle_exception(e)


@router.delete("/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    share_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoquer un partage."""
    service = get_service(db, current_user)
    if not service.revoke_share(share_id, current_user.id):
        raise HTTPException(status_code=404, detail="Partage non trouve")


# =============================================================================
# ENDPOINTS LIENS ENTITES
# =============================================================================

@router.post("/{document_id}/links", response_model=DocumentLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_to_entity(
    document_id: UUID,
    data: DocumentLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lier un document a une entite."""
    service = get_service(db, current_user)
    try:
        return service.link_to_entity(document_id, data, current_user.id)
    except Exception as e:
        handle_exception(e)


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[DocumentResponse])
async def get_entity_documents(
    entity_type: LinkEntityType,
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les documents lies a une entite."""
    service = get_service(db, current_user)
    return service.get_entity_documents(entity_type, entity_id)


@router.delete("/{document_id}/links/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_from_entity(
    document_id: UUID,
    entity_type: LinkEntityType,
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer le lien entre un document et une entite."""
    service = get_service(db, current_user)
    if not service.unlink_from_entity(document_id, entity_type, entity_id):
        raise HTTPException(status_code=404, detail="Lien non trouve")


# =============================================================================
# ENDPOINTS RECHERCHE
# =============================================================================

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    query: SearchQuery,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rechercher dans les documents."""
    service = get_service(db, current_user)
    return service.search(query, page, page_size)


# =============================================================================
# ENDPOINTS COMMENTAIRES
# =============================================================================

@router.post("/{document_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    document_id: UUID,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter un commentaire."""
    service = get_service(db, current_user)
    try:
        return service.add_comment(document_id, data, current_user.id)
    except Exception as e:
        handle_exception(e)


@router.get("/{document_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les commentaires d'un document."""
    service = get_service(db, current_user)
    return service.get_comments(document_id)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un commentaire."""
    service = get_service(db, current_user)
    if not service.delete_comment(comment_id, current_user.id):
        raise HTTPException(status_code=404, detail="Commentaire non trouve")


# =============================================================================
# ENDPOINTS TAGS ET CATEGORIES
# =============================================================================

@router.post("/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un tag."""
    service = get_service(db, current_user)
    return service.create_tag(data, current_user.id)


@router.get("/tags", response_model=List[TagResponse])
async def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les tags."""
    service = get_service(db, current_user)
    return service.get_tags()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une categorie."""
    service = get_service(db, current_user)
    try:
        return service.create_category(data, current_user.id)
    except Exception as e:
        handle_exception(e)


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les categories."""
    service = get_service(db, current_user)
    return service.get_categories()


# =============================================================================
# ENDPOINTS OPERATIONS EN LOT
# =============================================================================

@router.post("/batch/move", response_model=BatchOperationResult)
async def batch_move(
    data: BatchMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deplacer plusieurs documents."""
    service = get_service(db, current_user)
    return service.batch_move(data.document_ids, data.target_folder_id, current_user.id)


@router.post("/batch/delete", response_model=BatchOperationResult)
async def batch_delete(
    data: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer plusieurs documents."""
    service = get_service(db, current_user)
    return service.batch_delete(data.document_ids, data.permanent, current_user.id)


@router.post("/batch/tag", response_model=BatchOperationResult)
async def batch_tag(
    data: BatchTagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter des tags a plusieurs documents."""
    service = get_service(db, current_user)
    return service.batch_tag(data.document_ids, data.tags, data.replace, current_user.id)


@router.post("/batch/archive", response_model=UploadResponse)
async def batch_archive(
    document_ids: List[UUID],
    archive_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archiver plusieurs documents dans un ZIP."""
    service = get_service(db, current_user)
    try:
        return service.archive_documents(document_ids, archive_name, current_user.id)
    except Exception as e:
        handle_exception(e)


# =============================================================================
# ENDPOINTS STATISTIQUES ET AUDIT
# =============================================================================

@router.get("/stats", response_model=StorageStats)
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir les statistiques de stockage."""
    service = get_service(db, current_user)
    return service.get_storage_stats()


@router.get("/{document_id}/audit", response_model=AuditList)
async def get_audit_history(
    document_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir l'historique d'audit d'un document."""
    service = get_service(db, current_user)
    items, total = service.get_audit_history(document_id, page, page_size)
    pages = (total + page_size - 1) // page_size

    return AuditList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


# =============================================================================
# ENDPOINTS MAINTENANCE (Admin)
# =============================================================================

@router.post("/admin/purge", response_model=dict)
async def purge_deleted_documents(
    older_than_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Purger les documents supprimes depuis plus de X jours."""
    require_admin_role(current_user)
    service = get_service(db, current_user)
    count = service.purge_deleted_documents(older_than_days)
    return {"purged_count": count}


@router.post("/admin/retention", response_model=dict)
async def apply_retention_policy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Appliquer les politiques de retention."""
    require_admin_role(current_user)
    service = get_service(db, current_user)
    count = service.apply_retention_policy()
    return {"archived_count": count}
