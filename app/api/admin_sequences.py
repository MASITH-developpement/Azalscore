"""
AZALSCORE - API Administration des Sequences
=============================================

Endpoints pour parametrer les numerotations automatiques.
Accessible uniquement aux administrateurs.
"""
from __future__ import annotations


from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.core.sequences import SequenceGenerator, DEFAULT_SEQUENCES


router = APIRouter(prefix="/admin/sequences", tags=["Administration - Sequences"])


# ============================================================================
# SCHEMAS
# ============================================================================

class SequenceConfigResponse(BaseModel):
    """Configuration d'une sequence."""
    entity_type: str = Field(..., description="Type d'entite (CLIENT, FACTURE_VENTE, etc.)")
    prefix: str = Field(..., description="Prefixe de la reference (CLI, FV, etc.)")
    include_year: bool = Field(..., description="Inclure l'annee dans la reference")
    padding: int = Field(..., description="Nombre de chiffres (ex: 4 = 0001)")
    separator: str = Field("-", description="Separateur (-, /, .)")
    reset_yearly: bool = Field(..., description="Reinitialiser le compteur chaque annee")
    current_year: int = Field(..., description="Annee en cours")
    current_number: int = Field(..., description="Dernier numero utilise")
    configured: bool = Field(False, description="True si personnalise, False si valeur par defaut")
    example: Optional[str] = Field(None, description="Exemple de reference generee")

    class Config:
        from_attributes = True


class SequenceConfigUpdate(BaseModel):
    """Mise a jour d'une configuration de sequence."""
    prefix: Optional[str] = Field(None, min_length=1, max_length=10, description="Nouveau prefixe")
    include_year: Optional[bool] = Field(None, description="Inclure l'annee")
    padding: Optional[int] = Field(None, ge=1, le=10, description="Nombre de chiffres")
    separator: Optional[str] = Field(None, max_length=1, description="Separateur")
    reset_yearly: Optional[bool] = Field(None, description="Reset annuel")


class SequenceListResponse(BaseModel):
    """Liste des configurations de sequences."""
    items: list[SequenceConfigResponse]
    total: int


class EntityTypeInfo(BaseModel):
    """Information sur un type d'entite."""
    entity_type: str
    description: str
    module: str


# ============================================================================
# METADATA - Descriptions des types d'entites
# ============================================================================

ENTITY_DESCRIPTIONS = {
    # Commercial - Clients/Fournisseurs
    "CLIENT": {"description": "Clients", "module": "Commercial"},
    "FOURNISSEUR": {"description": "Fournisseurs", "module": "Achats"},
    "OPPORTUNITE": {"description": "Opportunites commerciales", "module": "CRM"},

    # Commercial - Documents vente
    "DEVIS": {"description": "Devis clients", "module": "Commercial"},
    "COMMANDE_CLIENT": {"description": "Commandes clients", "module": "Commercial"},
    "FACTURE_VENTE": {"description": "Factures de vente", "module": "Commercial"},
    "AVOIR_CLIENT": {"description": "Avoirs clients", "module": "Commercial"},
    "PROFORMA": {"description": "Factures proforma", "module": "Commercial"},
    "BON_LIVRAISON": {"description": "Bons de livraison", "module": "Commercial"},

    # Commercial - Documents achat
    "COMMANDE_FOURNISSEUR": {"description": "Commandes fournisseurs", "module": "Achats"},
    "FACTURE_ACHAT": {"description": "Factures d'achat", "module": "Achats"},
    "AVOIR_FOURNISSEUR": {"description": "Avoirs fournisseurs", "module": "Achats"},
    "BON_RECEPTION": {"description": "Bons de reception", "module": "Achats"},

    # RH
    "EMPLOYE": {"description": "Employes", "module": "RH"},

    # Interventions
    "INTERVENTION": {"description": "Interventions terrain", "module": "Interventions"},
    "DONNEUR_ORDRE": {"description": "Donneurs d'ordre", "module": "Interventions"},
    "RAPPORT_INTERVENTION": {"description": "Rapports d'intervention", "module": "Interventions"},

    # Projets
    "AFFAIRE": {"description": "Affaires/Dossiers", "module": "Projets"},
    "PROJET": {"description": "Projets", "module": "Projets"},

    # Maintenance
    "ORDRE_MAINTENANCE": {"description": "Ordres de maintenance (GMAO)", "module": "Maintenance"},

    # Qualite
    "NON_CONFORMITE": {"description": "Non-conformites", "module": "Qualite"},
    "REGLE_QC": {"description": "Regles de controle qualite", "module": "Qualite"},
    "INSPECTION": {"description": "Inspections/Controles", "module": "Qualite"},

    # Helpdesk
    "TICKET": {"description": "Tickets support client", "module": "Helpdesk"},
    "CATEGORIE_TICKET": {"description": "Categories de tickets", "module": "Helpdesk"},

    # Comptabilite
    "PIECE_COMPTABLE": {"description": "Pieces comptables", "module": "Comptabilite"},
    "EXERCICE": {"description": "Exercices comptables", "module": "Comptabilite"},
}


# ============================================================================
# HELPERS
# ============================================================================

def _generate_example(config: dict) -> str:
    """Genere un exemple de reference basee sur la configuration."""
    prefix = config["prefix"]
    separator = config.get("separator", "-")
    padding = config.get("padding", 4)
    include_year = config.get("include_year", True)
    current_year = config.get("current_year", 2026)
    next_number = config.get("current_number", 0) + 1

    if include_year:
        return f"{prefix}{separator}{current_year}{separator}{next_number:0{padding}d}"
    else:
        return f"{prefix}{separator}{next_number:0{padding}d}"


def _enrich_config(config: dict) -> dict:
    """Enrichit une configuration avec des metadonnees."""
    entity_type = config["entity_type"]
    meta = ENTITY_DESCRIPTIONS.get(entity_type, {"description": entity_type, "module": "Autre"})
    config["description"] = meta["description"]
    config["module"] = meta["module"]
    config["example"] = _generate_example(config)
    return config


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=SequenceListResponse)
async def list_sequences(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Liste toutes les configurations de sequences.

    Retourne les sequences personnalisees ET les sequences par defaut
    non encore configurees.
    """
    generator = SequenceGenerator(db, context.tenant_id)
    configs = generator.list_configs()

    # Enrichir avec descriptions et exemples
    enriched = [_enrich_config(c) for c in configs]

    return SequenceListResponse(
        items=enriched,
        total=len(enriched)
    )


@router.get("/entity-types", response_model=list[EntityTypeInfo])
async def list_entity_types(
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Liste les types d'entites disponibles avec leurs descriptions.

    SÉCURITÉ: Authentification requise.
    """
    return [
        EntityTypeInfo(
            entity_type=entity_type,
            description=info["description"],
            module=info["module"]
        )
        for entity_type, info in ENTITY_DESCRIPTIONS.items()
    ]


@router.get("/{entity_type}", response_model=SequenceConfigResponse)
async def get_sequence(
    entity_type: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Recupere la configuration d'une sequence specifique.
    """
    # Verifier que le type existe
    if entity_type not in DEFAULT_SEQUENCES and entity_type not in ENTITY_DESCRIPTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type d'entite inconnu: {entity_type}"
        )

    generator = SequenceGenerator(db, context.tenant_id)
    config = generator.get_config(entity_type)

    if not config:
        # Retourner les valeurs par defaut
        defaults = DEFAULT_SEQUENCES.get(entity_type, {
            "prefix": entity_type[:3].upper(),
            "include_year": True,
            "padding": 4,
            "reset_yearly": True
        })
        config = {
            "entity_type": entity_type,
            "prefix": defaults.get("prefix", entity_type[:3].upper()),
            "include_year": defaults.get("include_year", True),
            "padding": defaults.get("padding", 4),
            "separator": "-",
            "reset_yearly": defaults.get("reset_yearly", True),
            "current_year": 2026,
            "current_number": 0,
            "configured": False
        }
    else:
        config["configured"] = True

    return _enrich_config(config)


@router.put("/{entity_type}", response_model=SequenceConfigResponse)
async def update_sequence(
    entity_type: str,
    data: SequenceConfigUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Met a jour la configuration d'une sequence.

    Seuls les champs fournis sont mis a jour.
    Le compteur actuel n'est PAS modifiable via cette API.
    """
    # Verifier que le type existe
    if entity_type not in DEFAULT_SEQUENCES and entity_type not in ENTITY_DESCRIPTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type d'entite inconnu: {entity_type}"
        )

    generator = SequenceGenerator(db, context.tenant_id)

    # Mettre a jour
    config = generator.update_config(
        entity_type=entity_type,
        prefix=data.prefix,
        include_year=data.include_year,
        padding=data.padding,
        separator=data.separator,
        reset_yearly=data.reset_yearly
    )

    result = {
        "entity_type": config.entity_type,
        "prefix": config.prefix,
        "include_year": config.include_year,
        "padding": config.padding,
        "separator": config.separator,
        "reset_yearly": config.reset_yearly,
        "current_year": config.current_year,
        "current_number": config.current_number,
        "configured": True
    }

    return _enrich_config(result)


@router.post("/{entity_type}/reset", response_model=SequenceConfigResponse)
async def reset_sequence_to_defaults(
    entity_type: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Reinitialise une sequence aux valeurs par defaut.

    ATTENTION: Le compteur n'est PAS remis a zero, seuls les parametres
    de format sont reinitialises.
    """
    if entity_type not in DEFAULT_SEQUENCES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type d'entite inconnu ou sans valeur par defaut: {entity_type}"
        )

    defaults = DEFAULT_SEQUENCES[entity_type]
    generator = SequenceGenerator(db, context.tenant_id)

    config = generator.update_config(
        entity_type=entity_type,
        prefix=defaults["prefix"],
        include_year=defaults["include_year"],
        padding=defaults["padding"],
        separator="-",
        reset_yearly=defaults["reset_yearly"]
    )

    result = {
        "entity_type": config.entity_type,
        "prefix": config.prefix,
        "include_year": config.include_year,
        "padding": config.padding,
        "separator": config.separator,
        "reset_yearly": config.reset_yearly,
        "current_year": config.current_year,
        "current_number": config.current_number,
        "configured": True
    }

    return _enrich_config(result)


@router.get("/{entity_type}/preview")
async def preview_sequence(
    entity_type: str,
    prefix: Optional[str] = None,
    include_year: Optional[bool] = None,
    padding: Optional[int] = None,
    separator: Optional[str] = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Previsualise une reference avec les parametres specifies.

    Permet de tester le format avant de sauvegarder.
    """
    generator = SequenceGenerator(db, context.tenant_id)
    current_config = generator.get_config(entity_type)

    if not current_config:
        defaults = DEFAULT_SEQUENCES.get(entity_type, {
            "prefix": entity_type[:3].upper(),
            "include_year": True,
            "padding": 4,
            "reset_yearly": True
        })
        current_config = {
            "prefix": defaults.get("prefix", entity_type[:3].upper()),
            "include_year": defaults.get("include_year", True),
            "padding": defaults.get("padding", 4),
            "separator": "-",
            "current_year": 2026,
            "current_number": 0
        }

    # Appliquer les parametres de preview
    preview_config = {
        "prefix": prefix if prefix is not None else current_config.get("prefix", "XXX"),
        "include_year": include_year if include_year is not None else current_config.get("include_year", True),
        "padding": padding if padding is not None else current_config.get("padding", 4),
        "separator": separator if separator is not None else current_config.get("separator", "-"),
        "current_year": current_config.get("current_year", 2026),
        "current_number": current_config.get("current_number", 0)
    }

    example = _generate_example(preview_config)

    return {
        "entity_type": entity_type,
        "preview": example,
        "next_number": preview_config["current_number"] + 1,
        "config": preview_config
    }
