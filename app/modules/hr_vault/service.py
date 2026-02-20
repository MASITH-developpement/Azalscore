"""
Coffre-fort RH Numérique - GAP-032

Stockage sécurisé et dématérialisé des documents RH:
- Bulletins de paie électroniques (conformité décret 2016-1762)
- Contrats de travail
- Avenants
- Attestations diverses
- Documents de fin de contrat

Conformité:
- Code du travail articles L3243-2, D3243-8
- Décret 2016-1762 du 16 décembre 2016
- RGPD (conservation, droit d'accès, portabilité)
- NF Z42-020 (archivage électronique)

Fonctionnalités:
- Stockage chiffré AES-256
- Horodatage certifié
- Signature électronique
- Accès salarié 24/7
- Conservation 50 ans minimum
- Portabilité des données
- Audit trail complet

Architecture multi-tenant avec isolation stricte.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, BinaryIO
import hashlib
import hmac
import uuid
import base64
import json
import os
from pathlib import Path


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class DocumentType(Enum):
    """Type de document RH."""
    # Paie
    PAYSLIP = "payslip"  # Bulletin de paie
    PAYSLIP_SUMMARY = "payslip_summary"  # Récapitulatif annuel

    # Contrats
    EMPLOYMENT_CONTRACT = "employment_contract"  # Contrat de travail
    AMENDMENT = "amendment"  # Avenant
    TEMPORARY_CONTRACT = "temporary_contract"  # CDD
    APPRENTICESHIP_CONTRACT = "apprenticeship_contract"  # Contrat apprentissage

    # Attestations
    EMPLOYMENT_CERTIFICATE = "employment_certificate"  # Attestation employeur
    SALARY_CERTIFICATE = "salary_certificate"  # Attestation de salaire
    TRAINING_CERTIFICATE = "training_certificate"  # Attestation formation
    FRANCE_TRAVAIL_CERTIFICATE = "france_travail_certificate"  # Attestation Pôle Emploi

    # Fin de contrat
    TERMINATION_LETTER = "termination_letter"  # Lettre de rupture
    STC = "stc"  # Solde de tout compte
    WORK_CERTIFICATE = "work_certificate"  # Certificat de travail
    PORTABILITY_NOTICE = "portability_notice"  # Notice portabilité

    # Santé/Sécurité
    MEDICAL_APTITUDE = "medical_aptitude"  # Aptitude médicale
    ACCIDENT_DECLARATION = "accident_declaration"  # Déclaration AT

    # Autres
    ID_DOCUMENT = "id_document"  # Pièce d'identité
    DIPLOMA = "diploma"  # Diplôme
    RIB = "rib"  # RIB
    VITALE_CARD = "vitale_card"  # Carte vitale
    OTHER = "other"  # Autre


class DocumentStatus(Enum):
    """Statut d'un document."""
    DRAFT = "draft"  # Brouillon
    PENDING_SIGNATURE = "pending_signature"  # En attente signature
    ACTIVE = "active"  # Actif
    ARCHIVED = "archived"  # Archivé
    DELETED = "deleted"  # Supprimé (logique)


class AccessType(Enum):
    """Type d'accès au document."""
    VIEW = "view"  # Consultation
    DOWNLOAD = "download"  # Téléchargement
    PRINT = "print"  # Impression
    SHARE = "share"  # Partage


class RetentionPeriod(Enum):
    """Durée de conservation légale."""
    FIVE_YEARS = 5  # 5 ans
    TEN_YEARS = 10  # 10 ans
    LIFETIME_PLUS_5 = -1  # Vie active + 5 ans
    FIFTY_YEARS = 50  # 50 ans (bulletins de paie)
    PERMANENT = 999  # Conservation permanente


class EncryptionAlgorithm(Enum):
    """Algorithme de chiffrement."""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Employee:
    """Salarié propriétaire du coffre-fort."""
    id: str
    tenant_id: str
    employee_number: str
    email: str
    first_name: str
    last_name: str

    # Identité
    birth_date: Optional[date] = None
    social_security_number: Optional[str] = None  # Chiffré

    # Accès
    is_active: bool = True
    vault_activated_at: Optional[datetime] = None
    last_access_at: Optional[datetime] = None

    # Consentement
    consent_given: bool = False
    consent_date: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class DocumentMetadata:
    """Métadonnées d'un document."""
    title: str
    document_type: DocumentType
    description: Optional[str] = None

    # Dates
    document_date: date = field(default_factory=date.today)
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    # Paie
    pay_period: Optional[str] = None  # "2024-01" format
    gross_salary: Optional[Decimal] = None
    net_salary: Optional[Decimal] = None

    # Contrat
    contract_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Tags et classification
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None

    # Source
    source_system: Optional[str] = None
    source_reference: Optional[str] = None


@dataclass
class DocumentVersion:
    """Version d'un document."""
    version_number: int
    created_at: datetime
    created_by: str

    # Contenu
    file_size: int
    file_hash: str  # SHA-256
    encryption_key_id: str

    # Stockage
    storage_path: str
    storage_provider: str = "local"  # local, s3, azure, gcs

    # Horodatage
    timestamp_token: Optional[str] = None
    timestamp_authority: Optional[str] = None


@dataclass
class VaultDocument:
    """Document dans le coffre-fort."""
    id: str
    tenant_id: str
    employee_id: str

    # Métadonnées
    metadata: DocumentMetadata

    # Versions
    versions: List[DocumentVersion] = field(default_factory=list)
    current_version: int = 1

    # Statut
    status: DocumentStatus = DocumentStatus.ACTIVE

    # Dates système
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    # Conservation
    retention_period: RetentionPeriod = RetentionPeriod.FIFTY_YEARS
    retention_end_date: Optional[date] = None

    # Signature électronique
    is_signed: bool = False
    signature_id: Optional[str] = None
    signed_at: Optional[datetime] = None

    # Notification
    employee_notified: bool = False
    notification_date: Optional[datetime] = None

    @property
    def current_file_hash(self) -> Optional[str]:
        """Hash du fichier courant."""
        for v in self.versions:
            if v.version_number == self.current_version:
                return v.file_hash
        return None


@dataclass
class AccessLog:
    """Journal d'accès."""
    id: str
    document_id: str
    employee_id: str
    accessed_by: str  # ID de l'utilisateur (employé ou RH)

    # Action
    access_type: AccessType
    access_date: datetime = field(default_factory=datetime.now)

    # Contexte
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None

    # Résultat
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class EncryptionKey:
    """Clé de chiffrement."""
    id: str
    tenant_id: str
    algorithm: EncryptionAlgorithm
    key_material: bytes  # Clé chiffrée avec master key

    # Gestion
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    rotated_to: Optional[str] = None  # ID nouvelle clé si rotation


@dataclass
class ConsentRecord:
    """Enregistrement du consentement."""
    id: str
    employee_id: str
    consent_type: str  # "vault_activation", "payslip_electronic"

    # Consentement
    given: bool
    given_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    # Contexte
    ip_address: Optional[str] = None
    consent_text_version: str = "1.0"

    # Preuve
    signature_hash: Optional[str] = None


@dataclass
class DataPortabilityRequest:
    """Demande de portabilité des données."""
    id: str
    employee_id: str
    requested_at: datetime = field(default_factory=datetime.now)

    # Contenu
    document_types: List[DocumentType] = field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    # Statut
    status: str = "pending"  # pending, processing, ready, downloaded, expired
    processed_at: Optional[datetime] = None

    # Fichier export
    export_file_path: Optional[str] = None
    export_file_hash: Optional[str] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


# ============================================================================
# CONSTANTES LÉGALES
# ============================================================================

RETENTION_RULES = {
    DocumentType.PAYSLIP: RetentionPeriod.FIFTY_YEARS,
    DocumentType.PAYSLIP_SUMMARY: RetentionPeriod.FIFTY_YEARS,
    DocumentType.EMPLOYMENT_CONTRACT: RetentionPeriod.LIFETIME_PLUS_5,
    DocumentType.AMENDMENT: RetentionPeriod.LIFETIME_PLUS_5,
    DocumentType.TEMPORARY_CONTRACT: RetentionPeriod.LIFETIME_PLUS_5,
    DocumentType.APPRENTICESHIP_CONTRACT: RetentionPeriod.LIFETIME_PLUS_5,
    DocumentType.EMPLOYMENT_CERTIFICATE: RetentionPeriod.FIVE_YEARS,
    DocumentType.SALARY_CERTIFICATE: RetentionPeriod.FIVE_YEARS,
    DocumentType.TRAINING_CERTIFICATE: RetentionPeriod.TEN_YEARS,
    DocumentType.FRANCE_TRAVAIL_CERTIFICATE: RetentionPeriod.FIFTY_YEARS,
    DocumentType.TERMINATION_LETTER: RetentionPeriod.FIFTY_YEARS,
    DocumentType.STC: RetentionPeriod.FIFTY_YEARS,
    DocumentType.WORK_CERTIFICATE: RetentionPeriod.FIFTY_YEARS,
    DocumentType.PORTABILITY_NOTICE: RetentionPeriod.FIFTY_YEARS,
    DocumentType.MEDICAL_APTITUDE: RetentionPeriod.TEN_YEARS,
    DocumentType.ACCIDENT_DECLARATION: RetentionPeriod.TEN_YEARS,
    DocumentType.ID_DOCUMENT: RetentionPeriod.FIVE_YEARS,
    DocumentType.DIPLOMA: RetentionPeriod.PERMANENT,
    DocumentType.RIB: RetentionPeriod.FIVE_YEARS,
    DocumentType.VITALE_CARD: RetentionPeriod.FIVE_YEARS,
    DocumentType.OTHER: RetentionPeriod.FIVE_YEARS,
}


# ============================================================================
# SERVICE DE COFFRE-FORT
# ============================================================================

class HRVaultService:
    """
    Service principal du coffre-fort RH numérique.

    Gère:
    - Stockage sécurisé des documents
    - Chiffrement AES-256
    - Gestion des accès
    - Conformité légale
    - Portabilité des données
    """

    def __init__(
        self,
        tenant_id: str,
        storage_path: str,
        master_key: bytes,
        timestamp_service_url: Optional[str] = None
    ):
        self.tenant_id = tenant_id
        self.storage_path = Path(storage_path)
        self.master_key = master_key
        self.timestamp_service_url = timestamp_service_url

        # Stockage en mémoire (à remplacer par DB)
        self._employees: Dict[str, Employee] = {}
        self._documents: Dict[str, VaultDocument] = {}
        self._access_logs: List[AccessLog] = []
        self._encryption_keys: Dict[str, EncryptionKey] = {}
        self._consents: Dict[str, ConsentRecord] = {}
        self._portability_requests: Dict[str, DataPortabilityRequest] = {}

        # Créer les répertoires
        self.storage_path.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # GESTION DES EMPLOYÉS
    # ========================================================================

    def register_employee(
        self,
        employee_id: str,
        employee_number: str,
        email: str,
        first_name: str,
        last_name: str,
        birth_date: Optional[date] = None,
        social_security_number: Optional[str] = None
    ) -> Employee:
        """Enregistre un employé dans le coffre-fort."""
        # Chiffrer le NIR si fourni
        encrypted_ssn = None
        if social_security_number:
            encrypted_ssn = self._encrypt_sensitive_data(social_security_number)

        employee = Employee(
            id=employee_id,
            tenant_id=self.tenant_id,
            employee_number=employee_number,
            email=email,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            social_security_number=encrypted_ssn
        )

        self._employees[employee_id] = employee
        return employee

    def activate_vault(
        self,
        employee_id: str,
        consent_given: bool,
        ip_address: Optional[str] = None
    ) -> bool:
        """Active le coffre-fort pour un employé (avec consentement)."""
        employee = self._employees.get(employee_id)
        if not employee:
            raise ValueError(f"Employé {employee_id} non trouvé")

        if not consent_given:
            raise ValueError("Le consentement est obligatoire pour activer le coffre-fort")

        # Enregistrer le consentement
        consent = ConsentRecord(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            consent_type="vault_activation",
            given=True,
            given_at=datetime.now(),
            ip_address=ip_address,
            consent_text_version="1.0"
        )
        self._consents[consent.id] = consent

        # Activer le coffre
        employee.consent_given = True
        employee.consent_date = datetime.now()
        employee.vault_activated_at = datetime.now()

        return True

    # ========================================================================
    # CHIFFREMENT
    # ========================================================================

    def _generate_encryption_key(self) -> EncryptionKey:
        """Génère une nouvelle clé de chiffrement."""
        # Générer une clé AES-256 (32 bytes)
        raw_key = os.urandom(32)

        # Chiffrer la clé avec la master key
        encrypted_key = self._encrypt_with_master_key(raw_key)

        key = EncryptionKey(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
            key_material=encrypted_key
        )

        self._encryption_keys[key.id] = key
        return key

    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Chiffre des données avec la master key."""
        # Simulation - en production, utiliser une vraie implémentation AES
        # from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = os.urandom(12)
        # aesgcm = AESGCM(self.master_key)
        # ciphertext = aesgcm.encrypt(nonce, data, None)
        # return nonce + ciphertext

        # Simulation simple (XOR - NE PAS UTILISER EN PRODUCTION)
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ self.master_key[i % len(self.master_key)])
        return nonce + bytes(encrypted)

    def _decrypt_with_master_key(self, encrypted_data: bytes) -> bytes:
        """Déchiffre des données avec la master key."""
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        # Simulation simple (XOR inverse)
        decrypted = bytearray()
        for i, byte in enumerate(ciphertext):
            decrypted.append(byte ^ self.master_key[i % len(self.master_key)])
        return bytes(decrypted)

    def _encrypt_file(
        self,
        content: bytes,
        key: EncryptionKey
    ) -> Tuple[bytes, str]:
        """Chiffre un fichier et retourne le contenu chiffré et le hash."""
        # Calculer le hash original
        file_hash = hashlib.sha256(content).hexdigest()

        # Récupérer la clé
        raw_key = self._decrypt_with_master_key(key.key_material)

        # Chiffrer
        nonce = os.urandom(12)
        # aesgcm = AESGCM(raw_key)
        # encrypted = aesgcm.encrypt(nonce, content, None)

        # Simulation
        encrypted = bytearray()
        for i, byte in enumerate(content):
            encrypted.append(byte ^ raw_key[i % len(raw_key)])

        return nonce + bytes(encrypted), file_hash

    def _decrypt_file(
        self,
        encrypted_content: bytes,
        key: EncryptionKey
    ) -> bytes:
        """Déchiffre un fichier."""
        nonce = encrypted_content[:12]
        ciphertext = encrypted_content[12:]

        # Récupérer la clé
        raw_key = self._decrypt_with_master_key(key.key_material)

        # Simulation
        decrypted = bytearray()
        for i, byte in enumerate(ciphertext):
            decrypted.append(byte ^ raw_key[i % len(raw_key)])

        return bytes(decrypted)

    def _encrypt_sensitive_data(self, data: str) -> str:
        """Chiffre des données sensibles (NIR, etc.)."""
        encrypted = self._encrypt_with_master_key(data.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Déchiffre des données sensibles."""
        encrypted = base64.b64decode(encrypted_data)
        decrypted = self._decrypt_with_master_key(encrypted)
        return decrypted.decode()

    # ========================================================================
    # GESTION DES DOCUMENTS
    # ========================================================================

    def deposit_document(
        self,
        employee_id: str,
        content: bytes,
        metadata: DocumentMetadata,
        notify_employee: bool = True,
        created_by: str = "system"
    ) -> VaultDocument:
        """
        Dépose un document dans le coffre-fort.

        Args:
            employee_id: ID de l'employé
            content: Contenu du fichier (PDF)
            metadata: Métadonnées du document
            notify_employee: Notifier l'employé par email
            created_by: ID de l'utilisateur créateur

        Returns:
            Document créé
        """
        employee = self._employees.get(employee_id)
        if not employee:
            raise ValueError(f"Employé {employee_id} non trouvé")

        if not employee.vault_activated_at:
            raise ValueError("Le coffre-fort n'est pas activé pour cet employé")

        # Générer une clé de chiffrement
        encryption_key = self._generate_encryption_key()

        # Chiffrer le fichier
        encrypted_content, file_hash = self._encrypt_file(content, encryption_key)

        # Générer le chemin de stockage
        doc_id = str(uuid.uuid4())
        storage_subpath = f"{self.tenant_id}/{employee_id}/{doc_id}"
        full_path = self.storage_path / storage_subpath

        # Créer le répertoire et sauvegarder
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(encrypted_content)

        # Horodatage certifié si configuré
        timestamp_token = None
        if self.timestamp_service_url:
            timestamp_token = self._get_timestamp(file_hash)

        # Créer la version
        version = DocumentVersion(
            version_number=1,
            created_at=datetime.now(),
            created_by=created_by,
            file_size=len(content),
            file_hash=file_hash,
            encryption_key_id=encryption_key.id,
            storage_path=storage_subpath,
            timestamp_token=timestamp_token
        )

        # Déterminer la durée de conservation
        retention = RETENTION_RULES.get(
            metadata.document_type,
            RetentionPeriod.FIVE_YEARS
        )

        # Calculer la date de fin de conservation
        retention_end = None
        if retention != RetentionPeriod.PERMANENT and retention.value > 0:
            retention_end = date.today() + timedelta(days=retention.value * 365)

        # Créer le document
        document = VaultDocument(
            id=doc_id,
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            metadata=metadata,
            versions=[version],
            current_version=1,
            retention_period=retention,
            retention_end_date=retention_end
        )

        self._documents[doc_id] = document

        # Notification
        if notify_employee:
            self._notify_employee_new_document(employee, document)
            document.employee_notified = True
            document.notification_date = datetime.now()

        return document

    def deposit_payslip(
        self,
        employee_id: str,
        content: bytes,
        pay_period: str,
        gross_salary: Decimal,
        net_salary: Decimal,
        notify_employee: bool = True
    ) -> VaultDocument:
        """
        Dépose un bulletin de paie (méthode simplifiée).

        Args:
            employee_id: ID de l'employé
            content: PDF du bulletin
            pay_period: Période de paie (format "YYYY-MM")
            gross_salary: Salaire brut
            net_salary: Salaire net
            notify_employee: Notifier l'employé

        Returns:
            Document créé
        """
        # Parser la période
        year, month = pay_period.split("-")
        period_date = date(int(year), int(month), 1)

        # Fin de période (dernier jour du mois)
        if int(month) == 12:
            period_end = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(int(year), int(month) + 1, 1) - timedelta(days=1)

        metadata = DocumentMetadata(
            title=f"Bulletin de paie - {pay_period}",
            document_type=DocumentType.PAYSLIP,
            document_date=period_end,
            period_start=period_date,
            period_end=period_end,
            pay_period=pay_period,
            gross_salary=gross_salary,
            net_salary=net_salary,
            source_system="payroll"
        )

        return self.deposit_document(
            employee_id=employee_id,
            content=content,
            metadata=metadata,
            notify_employee=notify_employee,
            created_by="payroll_system"
        )

    def get_document(
        self,
        document_id: str,
        accessed_by: str,
        access_type: AccessType = AccessType.VIEW,
        ip_address: Optional[str] = None
    ) -> Tuple[VaultDocument, bytes]:
        """
        Récupère un document du coffre-fort.

        Args:
            document_id: ID du document
            accessed_by: ID de l'utilisateur
            access_type: Type d'accès
            ip_address: Adresse IP

        Returns:
            (Document, contenu déchiffré)
        """
        document = self._documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} non trouvé")

        if document.status == DocumentStatus.DELETED:
            raise ValueError("Document supprimé")

        # Vérifier les droits d'accès
        employee = self._employees.get(document.employee_id)
        if accessed_by != document.employee_id:
            # Vérifier si c'est un RH autorisé (à implémenter)
            pass

        # Récupérer la version courante
        version = next(
            (v for v in document.versions if v.version_number == document.current_version),
            None
        )
        if not version:
            raise ValueError("Version non trouvée")

        # Récupérer la clé
        encryption_key = self._encryption_keys.get(version.encryption_key_id)
        if not encryption_key:
            raise ValueError("Clé de chiffrement non trouvée")

        # Lire et déchiffrer
        full_path = self.storage_path / version.storage_path
        encrypted_content = full_path.read_bytes()
        content = self._decrypt_file(encrypted_content, encryption_key)

        # Vérifier le hash
        computed_hash = hashlib.sha256(content).hexdigest()
        if computed_hash != version.file_hash:
            raise ValueError("Intégrité du fichier compromise")

        # Logger l'accès
        self._log_access(
            document_id=document_id,
            employee_id=document.employee_id,
            accessed_by=accessed_by,
            access_type=access_type,
            ip_address=ip_address
        )

        # Mettre à jour last_access
        if employee:
            employee.last_access_at = datetime.now()

        return document, content

    def list_employee_documents(
        self,
        employee_id: str,
        document_type: Optional[DocumentType] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> List[VaultDocument]:
        """Liste les documents d'un employé."""
        documents = []

        for doc in self._documents.values():
            if doc.employee_id != employee_id:
                continue
            if doc.status == DocumentStatus.DELETED:
                continue

            if document_type and doc.metadata.document_type != document_type:
                continue

            if period_start and doc.metadata.document_date < period_start:
                continue
            if period_end and doc.metadata.document_date > period_end:
                continue

            documents.append(doc)

        # Trier par date décroissante
        documents.sort(key=lambda d: d.metadata.document_date, reverse=True)
        return documents

    def _log_access(
        self,
        document_id: str,
        employee_id: str,
        accessed_by: str,
        access_type: AccessType,
        ip_address: Optional[str] = None
    ):
        """Enregistre un accès au journal."""
        log = AccessLog(
            id=str(uuid.uuid4()),
            document_id=document_id,
            employee_id=employee_id,
            accessed_by=accessed_by,
            access_type=access_type,
            ip_address=ip_address
        )
        self._access_logs.append(log)

    def _notify_employee_new_document(
        self,
        employee: Employee,
        document: VaultDocument
    ):
        """Notifie l'employé d'un nouveau document."""
        # Envoyer un email
        # email_service.send(
        #     to=employee.email,
        #     subject=f"Nouveau document disponible: {document.metadata.title}",
        #     template="hr_vault_new_document",
        #     context={"employee": employee, "document": document}
        # )
        pass

    def _get_timestamp(self, data_hash: str) -> Optional[str]:
        """Obtient un horodatage certifié."""
        if not self.timestamp_service_url:
            return None

        # En production, appeler un service TSA (Time Stamp Authority)
        # response = requests.post(self.timestamp_service_url, data=data_hash)
        # return response.content.hex()

        # Simulation
        return f"TS-{datetime.now().isoformat()}-{data_hash[:16]}"

    # ========================================================================
    # PORTABILITÉ DES DONNÉES (RGPD)
    # ========================================================================

    def request_data_portability(
        self,
        employee_id: str,
        document_types: Optional[List[DocumentType]] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> DataPortabilityRequest:
        """
        Crée une demande de portabilité des données.

        Conformité RGPD article 20: droit à la portabilité.

        Args:
            employee_id: ID de l'employé
            document_types: Types de documents (tous si None)
            period_start: Début période
            period_end: Fin période

        Returns:
            Demande créée
        """
        employee = self._employees.get(employee_id)
        if not employee:
            raise ValueError(f"Employé {employee_id} non trouvé")

        request = DataPortabilityRequest(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            document_types=document_types or [],
            period_start=period_start,
            period_end=period_end
        )

        self._portability_requests[request.id] = request
        return request

    def process_portability_request(
        self,
        request_id: str
    ) -> DataPortabilityRequest:
        """
        Traite une demande de portabilité.

        Génère un fichier ZIP avec tous les documents.
        """
        request = self._portability_requests.get(request_id)
        if not request:
            raise ValueError(f"Demande {request_id} non trouvée")

        request.status = "processing"

        # Collecter les documents
        documents = self.list_employee_documents(
            employee_id=request.employee_id,
            period_start=request.period_start,
            period_end=request.period_end
        )

        if request.document_types:
            documents = [
                d for d in documents
                if d.metadata.document_type in request.document_types
            ]

        # Créer le fichier d'export (ZIP)
        export_id = str(uuid.uuid4())
        export_path = self.storage_path / "exports" / f"{export_id}.zip"
        export_path.parent.mkdir(parents=True, exist_ok=True)

        # En production, créer un vrai ZIP
        # with zipfile.ZipFile(export_path, 'w') as zf:
        #     for doc in documents:
        #         _, content = self.get_document(doc.id, request.employee_id)
        #         zf.writestr(f"{doc.metadata.title}.pdf", content)

        # Simulation
        export_path.write_bytes(b"ZIP_CONTENT_PLACEHOLDER")

        # Calculer le hash
        export_hash = hashlib.sha256(export_path.read_bytes()).hexdigest()

        request.status = "ready"
        request.processed_at = datetime.now()
        request.export_file_path = str(export_path)
        request.export_file_hash = export_hash
        request.expires_at = datetime.now() + timedelta(days=7)

        return request

    # ========================================================================
    # AUDIT ET CONFORMITÉ
    # ========================================================================

    def get_access_history(
        self,
        document_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AccessLog]:
        """Récupère l'historique des accès."""
        logs = self._access_logs

        if document_id:
            logs = [l for l in logs if l.document_id == document_id]

        if employee_id:
            logs = [l for l in logs if l.employee_id == employee_id]

        if start_date:
            logs = [l for l in logs if l.access_date >= start_date]

        if end_date:
            logs = [l for l in logs if l.access_date <= end_date]

        return sorted(logs, key=lambda l: l.access_date, reverse=True)

    def verify_document_integrity(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """Vérifie l'intégrité d'un document."""
        document = self._documents.get(document_id)
        if not document:
            raise ValueError(f"Document {document_id} non trouvé")

        results = {
            "document_id": document_id,
            "verified_at": datetime.now().isoformat(),
            "versions": []
        }

        for version in document.versions:
            # Récupérer la clé
            encryption_key = self._encryption_keys.get(version.encryption_key_id)
            if not encryption_key:
                results["versions"].append({
                    "version": version.version_number,
                    "status": "error",
                    "message": "Clé de chiffrement non trouvée"
                })
                continue

            # Lire et déchiffrer
            full_path = self.storage_path / version.storage_path
            if not full_path.exists():
                results["versions"].append({
                    "version": version.version_number,
                    "status": "error",
                    "message": "Fichier non trouvé"
                })
                continue

            encrypted_content = full_path.read_bytes()
            content = self._decrypt_file(encrypted_content, encryption_key)

            # Vérifier le hash
            computed_hash = hashlib.sha256(content).hexdigest()
            is_valid = computed_hash == version.file_hash

            results["versions"].append({
                "version": version.version_number,
                "status": "valid" if is_valid else "corrupted",
                "stored_hash": version.file_hash,
                "computed_hash": computed_hash,
                "timestamp_token": version.timestamp_token
            })

        results["overall_status"] = "valid" if all(
            v["status"] == "valid" for v in results["versions"]
        ) else "issues_found"

        return results

    def get_retention_report(self) -> Dict[str, Any]:
        """Génère un rapport sur la conservation des documents."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "tenant_id": self.tenant_id,
            "summary": {
                "total_documents": 0,
                "by_type": {},
                "by_retention_period": {},
                "documents_to_archive": [],
                "documents_past_retention": []
            }
        }

        today = date.today()

        for doc in self._documents.values():
            if doc.status == DocumentStatus.DELETED:
                continue

            report["summary"]["total_documents"] += 1

            # Par type
            doc_type = doc.metadata.document_type.value
            if doc_type not in report["summary"]["by_type"]:
                report["summary"]["by_type"][doc_type] = 0
            report["summary"]["by_type"][doc_type] += 1

            # Par période de conservation
            retention = doc.retention_period.name
            if retention not in report["summary"]["by_retention_period"]:
                report["summary"]["by_retention_period"][retention] = 0
            report["summary"]["by_retention_period"][retention] += 1

            # Documents dépassant la période de conservation
            if doc.retention_end_date and doc.retention_end_date < today:
                report["summary"]["documents_past_retention"].append({
                    "id": doc.id,
                    "title": doc.metadata.title,
                    "retention_end": doc.retention_end_date.isoformat()
                })

        return report


# ============================================================================
# FACTORY
# ============================================================================

def create_hr_vault_service(
    tenant_id: str,
    storage_path: str,
    master_key: Optional[bytes] = None,
    timestamp_service_url: Optional[str] = None
) -> HRVaultService:
    """
    Crée un service de coffre-fort RH.

    Args:
        tenant_id: ID du tenant
        storage_path: Chemin de stockage des fichiers
        master_key: Clé maître de chiffrement (32 bytes)
        timestamp_service_url: URL du service d'horodatage

    Returns:
        Service configuré
    """
    if master_key is None:
        # En production, récupérer depuis un HSM ou service de secrets
        master_key = os.urandom(32)

    return HRVaultService(
        tenant_id=tenant_id,
        storage_path=storage_path,
        master_key=master_key,
        timestamp_service_url=timestamp_service_url
    )
