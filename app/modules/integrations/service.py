"""
Service Intégrations et Connecteurs - GAP-054

Gestion des intégrations tierces:
- Connecteurs OAuth2/API Key
- Synchronisation bidirectionnelle
- Mapping des données
- Logs de synchronisation
- Gestion des conflits
- Monitoring des connexions
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4
import json


# ============================================================
# ÉNUMÉRATIONS
# ============================================================

class ConnectorType(Enum):
    """Types de connecteurs."""
    # Comptabilité
    SAGE = "sage"
    CEGID = "cegid"
    QUADRATUS = "quadratus"
    EBP = "ebp"
    PENNYLANE = "pennylane"

    # ERP
    ODOO = "odoo"
    SAP = "sap"
    DYNAMICS = "dynamics"
    NETSUITE = "netsuite"

    # CRM
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"

    # E-commerce
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    PRESTASHOP = "prestashop"
    MAGENTO = "magento"

    # Paiement
    STRIPE = "stripe"
    GOCARDLESS = "gocardless"
    MOLLIE = "mollie"

    # Banque
    SWAN = "swan"
    QONTO = "qonto"
    BRIDGE = "bridge"

    # Marketing
    MAILCHIMP = "mailchimp"
    SENDINBLUE = "sendinblue"
    MAILJET = "mailjet"

    # Documents
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"

    # Communication
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"

    # Autres
    ZAPIER = "zapier"
    MAKE = "make"
    CUSTOM = "custom"


class AuthType(Enum):
    """Types d'authentification."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    BEARER = "bearer"
    HMAC = "hmac"
    CERTIFICATE = "certificate"


class SyncDirection(Enum):
    """Direction de synchronisation."""
    IMPORT = "import"  # Externe → AZALSCORE
    EXPORT = "export"  # AZALSCORE → Externe
    BIDIRECTIONAL = "bidirectional"


class SyncFrequency(Enum):
    """Fréquence de synchronisation."""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class ConnectionStatus(Enum):
    """Statut de connexion."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"
    PENDING = "pending"


class SyncStatus(Enum):
    """Statut de synchronisation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConflictResolution(Enum):
    """Stratégies de résolution de conflits."""
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"
    MERGE = "merge"


class EntityType(Enum):
    """Types d'entités synchronisables."""
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PRODUCT = "product"
    ORDER = "order"
    INVOICE = "invoice"
    PAYMENT = "payment"
    TRANSACTION = "transaction"
    CONTACT = "contact"
    LEAD = "lead"
    OPPORTUNITY = "opportunity"
    PROJECT = "project"
    TASK = "task"
    TICKET = "ticket"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ConnectorDefinition:
    """Définition d'un connecteur."""
    connector_type: ConnectorType
    name: str
    description: str
    auth_type: AuthType
    base_url: str

    # Entités supportées
    supported_entities: List[EntityType] = field(default_factory=list)
    supported_directions: List[SyncDirection] = field(default_factory=list)

    # Configuration requise
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)

    # OAuth2
    oauth_authorize_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_scopes: List[str] = field(default_factory=list)

    # Rate limits
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 10000

    # Icône et documentation
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class Connection:
    """Connexion à un service externe."""
    id: str
    tenant_id: str
    connector_type: ConnectorType
    name: str

    # Authentification
    auth_type: AuthType
    credentials: Dict[str, str] = field(default_factory=dict)  # Chiffré en production

    # OAuth2
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

    # Configuration
    base_url: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

    # État
    status: ConnectionStatus = ConnectionStatus.PENDING
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


@dataclass
class FieldMapping:
    """Mapping d'un champ entre systèmes."""
    id: str
    source_field: str
    target_field: str

    # Transformation
    transform: Optional[str] = None  # Expression de transformation
    default_value: Optional[Any] = None
    is_required: bool = False

    # Conversion de type
    source_type: Optional[str] = None
    target_type: Optional[str] = None


@dataclass
class EntityMapping:
    """Mapping d'une entité entre systèmes."""
    id: str
    tenant_id: str
    connection_id: str
    entity_type: EntityType

    # Source et cible
    source_entity: str  # Nom de l'entité dans le système source
    target_entity: str  # Nom de l'entité dans AZALSCORE

    # Direction
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL

    # Mappings de champs
    field_mappings: List[FieldMapping] = field(default_factory=list)

    # Filtres
    source_filter: Optional[Dict[str, Any]] = None
    target_filter: Optional[Dict[str, Any]] = None

    # Clé de déduplication
    dedup_key_source: Optional[str] = None
    dedup_key_target: Optional[str] = None

    # État
    is_active: bool = True

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


@dataclass
class SyncJob:
    """Job de synchronisation."""
    id: str
    tenant_id: str
    connection_id: str
    entity_mapping_id: str

    # Configuration
    direction: SyncDirection
    conflict_resolution: ConflictResolution = ConflictResolution.NEWEST_WINS

    # Planification
    frequency: SyncFrequency = SyncFrequency.MANUAL
    next_run_at: Optional[datetime] = None
    cron_expression: Optional[str] = None

    # État
    status: SyncStatus = SyncStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Statistiques
    total_records: int = 0
    processed_records: int = 0
    created_records: int = 0
    updated_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0

    # Erreurs
    errors: List[Dict[str, Any]] = field(default_factory=list)

    # Delta sync
    last_sync_at: Optional[datetime] = None
    sync_cursor: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100


@dataclass
class SyncLog:
    """Log de synchronisation."""
    id: str
    tenant_id: str
    job_id: str

    # Enregistrement
    source_id: str
    target_id: Optional[str] = None
    entity_type: EntityType = EntityType.CUSTOMER

    # Action
    action: str = "create"  # create, update, skip, error

    # Données
    source_data: Optional[Dict[str, Any]] = None
    target_data: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None

    # Résultat
    success: bool = True
    error_message: Optional[str] = None

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Conflict:
    """Conflit de synchronisation."""
    id: str
    tenant_id: str
    job_id: str

    # Enregistrements en conflit
    source_id: str
    target_id: str
    entity_type: EntityType

    # Données
    source_data: Dict[str, Any] = field(default_factory=dict)
    target_data: Dict[str, Any] = field(default_factory=dict)

    # Champs en conflit
    conflicting_fields: List[str] = field(default_factory=list)

    # Résolution
    resolution: Optional[ConflictResolution] = None
    resolved_data: Optional[Dict[str, Any]] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    # Timestamp
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConnectionHealth:
    """État de santé d'une connexion."""
    connection_id: str
    is_healthy: bool
    last_check_at: datetime

    # Métriques
    response_time_ms: int = 0
    success_rate_24h: float = 100.0
    total_requests_24h: int = 0

    # Erreurs
    last_error: Optional[str] = None
    consecutive_errors: int = 0


# ============================================================
# DÉFINITIONS DES CONNECTEURS
# ============================================================

CONNECTOR_DEFINITIONS: Dict[ConnectorType, ConnectorDefinition] = {
    ConnectorType.STRIPE: ConnectorDefinition(
        connector_type=ConnectorType.STRIPE,
        name="Stripe",
        description="Plateforme de paiement en ligne",
        auth_type=AuthType.API_KEY,
        base_url="https://api.stripe.com/v1",
        supported_entities=[EntityType.PAYMENT, EntityType.CUSTOMER, EntityType.INVOICE],
        supported_directions=[SyncDirection.IMPORT, SyncDirection.EXPORT],
        required_fields=["api_key"],
        rate_limit_per_minute=100,
    ),
    ConnectorType.HUBSPOT: ConnectorDefinition(
        connector_type=ConnectorType.HUBSPOT,
        name="HubSpot",
        description="CRM et marketing automation",
        auth_type=AuthType.OAUTH2,
        base_url="https://api.hubspot.com",
        supported_entities=[EntityType.CONTACT, EntityType.CUSTOMER, EntityType.LEAD, EntityType.OPPORTUNITY],
        supported_directions=[SyncDirection.BIDIRECTIONAL],
        oauth_authorize_url="https://app.hubspot.com/oauth/authorize",
        oauth_token_url="https://api.hubspot.com/oauth/v1/token",
        oauth_scopes=["contacts", "crm.objects.contacts.read", "crm.objects.contacts.write"],
        rate_limit_per_minute=100,
    ),
    ConnectorType.SHOPIFY: ConnectorDefinition(
        connector_type=ConnectorType.SHOPIFY,
        name="Shopify",
        description="Plateforme e-commerce",
        auth_type=AuthType.OAUTH2,
        base_url="https://{shop}.myshopify.com/admin/api/2024-01",
        supported_entities=[EntityType.PRODUCT, EntityType.ORDER, EntityType.CUSTOMER],
        supported_directions=[SyncDirection.BIDIRECTIONAL],
        required_fields=["shop_domain"],
        oauth_scopes=["read_products", "write_products", "read_orders", "read_customers"],
        rate_limit_per_minute=40,
    ),
    ConnectorType.ODOO: ConnectorDefinition(
        connector_type=ConnectorType.ODOO,
        name="Odoo",
        description="ERP open source",
        auth_type=AuthType.API_KEY,
        base_url="https://{instance}/xmlrpc/2",
        supported_entities=[EntityType.CUSTOMER, EntityType.SUPPLIER, EntityType.PRODUCT, EntityType.ORDER, EntityType.INVOICE],
        supported_directions=[SyncDirection.BIDIRECTIONAL],
        required_fields=["instance_url", "database", "api_key"],
        rate_limit_per_minute=60,
    ),
    ConnectorType.SLACK: ConnectorDefinition(
        connector_type=ConnectorType.SLACK,
        name="Slack",
        description="Messagerie d'équipe",
        auth_type=AuthType.OAUTH2,
        base_url="https://slack.com/api",
        supported_entities=[],
        supported_directions=[SyncDirection.EXPORT],
        oauth_authorize_url="https://slack.com/oauth/v2/authorize",
        oauth_token_url="https://slack.com/api/oauth.v2.access",
        oauth_scopes=["chat:write", "channels:read"],
        rate_limit_per_minute=50,
    ),
    ConnectorType.MAILCHIMP: ConnectorDefinition(
        connector_type=ConnectorType.MAILCHIMP,
        name="Mailchimp",
        description="Email marketing",
        auth_type=AuthType.API_KEY,
        base_url="https://{dc}.api.mailchimp.com/3.0",
        supported_entities=[EntityType.CONTACT],
        supported_directions=[SyncDirection.EXPORT],
        required_fields=["api_key"],
        rate_limit_per_minute=10,
    ),
}


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class IntegrationService:
    """Service de gestion des intégrations."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (à remplacer par DB)
        self._connections: Dict[str, Connection] = {}
        self._entity_mappings: Dict[str, EntityMapping] = {}
        self._sync_jobs: Dict[str, SyncJob] = {}
        self._sync_logs: List[SyncLog] = []
        self._conflicts: Dict[str, Conflict] = {}
        self._health_checks: Dict[str, ConnectionHealth] = {}

        # Index pour recherche rapide
        self._external_id_index: Dict[str, Dict[str, str]] = {}  # connection_id -> external_id -> internal_id

    # ========================================
    # GESTION DES CONNECTEURS
    # ========================================

    def list_available_connectors(self) -> List[ConnectorDefinition]:
        """Liste les connecteurs disponibles."""
        return list(CONNECTOR_DEFINITIONS.values())

    def get_connector_definition(
        self,
        connector_type: ConnectorType
    ) -> Optional[ConnectorDefinition]:
        """Récupère la définition d'un connecteur."""
        return CONNECTOR_DEFINITIONS.get(connector_type)

    # ========================================
    # GESTION DES CONNEXIONS
    # ========================================

    def create_connection(
        self,
        connector_type: ConnectorType,
        name: str,
        credentials: Dict[str, str],
        **kwargs
    ) -> Connection:
        """Crée une connexion à un service externe."""
        definition = self.get_connector_definition(connector_type)
        if not definition:
            raise ValueError(f"Connecteur {connector_type} non supporté")

        # Vérifier les champs requis
        for field in definition.required_fields:
            if field not in credentials:
                raise ValueError(f"Champ requis manquant: {field}")

        connection = Connection(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            connector_type=connector_type,
            name=name,
            auth_type=definition.auth_type,
            credentials=credentials,
            base_url=kwargs.get("base_url", definition.base_url),
            custom_headers=kwargs.get("custom_headers", {}),
            settings=kwargs.get("settings", {}),
        )

        self._connections[connection.id] = connection
        self._external_id_index[connection.id] = {}

        return connection

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Récupère une connexion."""
        conn = self._connections.get(connection_id)
        if conn and conn.tenant_id == self.tenant_id:
            return conn
        return None

    def list_connections(
        self,
        connector_type: Optional[ConnectorType] = None,
        status: Optional[ConnectionStatus] = None
    ) -> List[Connection]:
        """Liste les connexions."""
        connections = [
            c for c in self._connections.values()
            if c.tenant_id == self.tenant_id
        ]

        if connector_type:
            connections = [c for c in connections if c.connector_type == connector_type]
        if status:
            connections = [c for c in connections if c.status == status]

        return sorted(connections, key=lambda x: x.created_at, reverse=True)

    def update_connection(
        self,
        connection_id: str,
        **kwargs
    ) -> Optional[Connection]:
        """Met à jour une connexion."""
        conn = self.get_connection(connection_id)
        if not conn:
            return None

        if "name" in kwargs:
            conn.name = kwargs["name"]
        if "credentials" in kwargs:
            conn.credentials.update(kwargs["credentials"])
        if "settings" in kwargs:
            conn.settings.update(kwargs["settings"])
        if "status" in kwargs:
            conn.status = kwargs["status"]

        conn.updated_at = datetime.now()
        return conn

    def delete_connection(self, connection_id: str) -> bool:
        """Supprime une connexion."""
        conn = self.get_connection(connection_id)
        if not conn:
            return False

        # Supprimer les mappings associés
        to_delete = [
            m.id for m in self._entity_mappings.values()
            if m.connection_id == connection_id
        ]
        for mapping_id in to_delete:
            del self._entity_mappings[mapping_id]

        # Supprimer l'index
        if connection_id in self._external_id_index:
            del self._external_id_index[connection_id]

        del self._connections[connection_id]
        return True

    def test_connection(self, connection_id: str) -> Tuple[bool, Optional[str]]:
        """Teste une connexion."""
        conn = self.get_connection(connection_id)
        if not conn:
            return False, "Connexion non trouvée"

        # Simuler un test (en production: vraie requête)
        import random
        start_time = datetime.now()

        if random.random() < 0.9:
            conn.status = ConnectionStatus.CONNECTED
            conn.last_connected_at = datetime.now()
            conn.last_error = None

            # Mettre à jour le health check
            self._update_health(connection_id, True, int((datetime.now() - start_time).total_seconds() * 1000))
            return True, None
        else:
            error = "Connection timeout"
            conn.status = ConnectionStatus.ERROR
            conn.last_error = error
            self._update_health(connection_id, False, 0, error)
            return False, error

    def _update_health(
        self,
        connection_id: str,
        is_healthy: bool,
        response_time_ms: int,
        error: Optional[str] = None
    ) -> None:
        """Met à jour le health check."""
        health = self._health_checks.get(connection_id)
        if not health:
            health = ConnectionHealth(
                connection_id=connection_id,
                is_healthy=is_healthy,
                last_check_at=datetime.now(),
            )
            self._health_checks[connection_id] = health

        health.is_healthy = is_healthy
        health.last_check_at = datetime.now()
        health.response_time_ms = response_time_ms
        health.last_error = error

        if is_healthy:
            health.consecutive_errors = 0
        else:
            health.consecutive_errors += 1

    # ========================================
    # OAUTH2
    # ========================================

    def get_oauth_url(
        self,
        connector_type: ConnectorType,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Optional[str]:
        """Génère l'URL d'autorisation OAuth2."""
        definition = self.get_connector_definition(connector_type)
        if not definition or not definition.oauth_authorize_url:
            return None

        import urllib.parse

        params = {
            "client_id": "{CLIENT_ID}",  # À remplacer par la vraie clé
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(definition.oauth_scopes),
        }

        if state:
            params["state"] = state

        return f"{definition.oauth_authorize_url}?{urllib.parse.urlencode(params)}"

    def exchange_oauth_code(
        self,
        connection_id: str,
        code: str,
        redirect_uri: str
    ) -> bool:
        """Échange un code OAuth2 contre des tokens."""
        conn = self.get_connection(connection_id)
        if not conn:
            return False

        # Simuler l'échange (en production: vraie requête)
        import secrets as py_secrets

        conn.access_token = py_secrets.token_urlsafe(32)
        conn.refresh_token = py_secrets.token_urlsafe(32)
        conn.token_expires_at = datetime.now() + timedelta(hours=1)
        conn.status = ConnectionStatus.CONNECTED
        conn.last_connected_at = datetime.now()
        conn.updated_at = datetime.now()

        return True

    def refresh_oauth_token(self, connection_id: str) -> bool:
        """Rafraîchit un token OAuth2."""
        conn = self.get_connection(connection_id)
        if not conn or not conn.refresh_token:
            return False

        # Simuler le rafraîchissement
        import secrets as py_secrets

        conn.access_token = py_secrets.token_urlsafe(32)
        conn.token_expires_at = datetime.now() + timedelta(hours=1)
        conn.updated_at = datetime.now()

        return True

    # ========================================
    # MAPPING DES ENTITÉS
    # ========================================

    def create_entity_mapping(
        self,
        connection_id: str,
        entity_type: EntityType,
        source_entity: str,
        target_entity: str,
        field_mappings: List[FieldMapping],
        **kwargs
    ) -> EntityMapping:
        """Crée un mapping d'entité."""
        conn = self.get_connection(connection_id)
        if not conn:
            raise ValueError("Connexion non trouvée")

        mapping = EntityMapping(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            connection_id=connection_id,
            entity_type=entity_type,
            source_entity=source_entity,
            target_entity=target_entity,
            direction=kwargs.get("direction", SyncDirection.BIDIRECTIONAL),
            field_mappings=field_mappings,
            source_filter=kwargs.get("source_filter"),
            target_filter=kwargs.get("target_filter"),
            dedup_key_source=kwargs.get("dedup_key_source"),
            dedup_key_target=kwargs.get("dedup_key_target"),
        )

        self._entity_mappings[mapping.id] = mapping
        return mapping

    def get_entity_mapping(self, mapping_id: str) -> Optional[EntityMapping]:
        """Récupère un mapping."""
        mapping = self._entity_mappings.get(mapping_id)
        if mapping and mapping.tenant_id == self.tenant_id:
            return mapping
        return None

    def list_entity_mappings(
        self,
        connection_id: Optional[str] = None,
        entity_type: Optional[EntityType] = None
    ) -> List[EntityMapping]:
        """Liste les mappings."""
        mappings = [
            m for m in self._entity_mappings.values()
            if m.tenant_id == self.tenant_id
        ]

        if connection_id:
            mappings = [m for m in mappings if m.connection_id == connection_id]
        if entity_type:
            mappings = [m for m in mappings if m.entity_type == entity_type]

        return mappings

    def transform_data(
        self,
        data: Dict[str, Any],
        mapping: EntityMapping,
        direction: SyncDirection
    ) -> Dict[str, Any]:
        """Transforme les données selon le mapping."""
        result = {}

        for field_mapping in mapping.field_mappings:
            if direction == SyncDirection.IMPORT:
                source_field = field_mapping.source_field
                target_field = field_mapping.target_field
            else:
                source_field = field_mapping.target_field
                target_field = field_mapping.source_field

            value = data.get(source_field)

            # Valeur par défaut
            if value is None and field_mapping.default_value is not None:
                value = field_mapping.default_value

            # Transformation (simplifié - en production: eval sécurisé)
            if value is not None and field_mapping.transform:
                # Exemple: "upper" pour mettre en majuscules
                if field_mapping.transform == "upper" and isinstance(value, str):
                    value = value.upper()
                elif field_mapping.transform == "lower" and isinstance(value, str):
                    value = value.lower()
                elif field_mapping.transform == "strip" and isinstance(value, str):
                    value = value.strip()

            if value is not None or field_mapping.is_required:
                result[target_field] = value

        return result

    # ========================================
    # SYNCHRONISATION
    # ========================================

    def create_sync_job(
        self,
        connection_id: str,
        entity_mapping_id: str,
        direction: SyncDirection,
        **kwargs
    ) -> SyncJob:
        """Crée un job de synchronisation."""
        conn = self.get_connection(connection_id)
        if not conn:
            raise ValueError("Connexion non trouvée")

        mapping = self.get_entity_mapping(entity_mapping_id)
        if not mapping:
            raise ValueError("Mapping non trouvé")

        job = SyncJob(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            connection_id=connection_id,
            entity_mapping_id=entity_mapping_id,
            direction=direction,
            conflict_resolution=kwargs.get("conflict_resolution", ConflictResolution.NEWEST_WINS),
            frequency=kwargs.get("frequency", SyncFrequency.MANUAL),
            cron_expression=kwargs.get("cron_expression"),
        )

        self._sync_jobs[job.id] = job
        return job

    def run_sync(self, job_id: str) -> SyncJob:
        """Exécute une synchronisation."""
        job = self._sync_jobs.get(job_id)
        if not job or job.tenant_id != self.tenant_id:
            raise ValueError("Job non trouvé")

        job.status = SyncStatus.RUNNING
        job.started_at = datetime.now()

        mapping = self.get_entity_mapping(job.entity_mapping_id)
        if not mapping:
            job.status = SyncStatus.FAILED
            job.errors.append({"error": "Mapping non trouvé"})
            return job

        # Simuler la synchronisation
        import random

        job.total_records = random.randint(10, 100)

        for i in range(job.total_records):
            job.processed_records += 1

            # Simuler différentes actions
            action = random.choice(["create", "update", "skip", "error"])

            if action == "create":
                job.created_records += 1
            elif action == "update":
                job.updated_records += 1
            elif action == "skip":
                job.skipped_records += 1
            else:
                job.failed_records += 1
                job.errors.append({
                    "record_index": i,
                    "error": "Erreur simulée"
                })

            # Logger
            self._sync_logs.append(SyncLog(
                id=str(uuid4()),
                tenant_id=self.tenant_id,
                job_id=job_id,
                source_id=f"ext_{i}",
                target_id=f"int_{i}" if action != "error" else None,
                entity_type=mapping.entity_type,
                action=action,
                success=(action != "error"),
                error_message="Erreur simulée" if action == "error" else None,
            ))

        job.status = SyncStatus.COMPLETED if job.failed_records == 0 else SyncStatus.PARTIAL
        job.completed_at = datetime.now()
        job.last_sync_at = datetime.now()

        return job

    def get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """Récupère un job."""
        job = self._sync_jobs.get(job_id)
        if job and job.tenant_id == self.tenant_id:
            return job
        return None

    def list_sync_jobs(
        self,
        connection_id: Optional[str] = None,
        status: Optional[SyncStatus] = None
    ) -> List[SyncJob]:
        """Liste les jobs."""
        jobs = [
            j for j in self._sync_jobs.values()
            if j.tenant_id == self.tenant_id
        ]

        if connection_id:
            jobs = [j for j in jobs if j.connection_id == connection_id]
        if status:
            jobs = [j for j in jobs if j.status == status]

        return sorted(jobs, key=lambda x: x.started_at or datetime.min, reverse=True)

    def get_sync_logs(
        self,
        job_id: str,
        limit: int = 100
    ) -> List[SyncLog]:
        """Récupère les logs d'un job."""
        logs = [
            l for l in self._sync_logs
            if l.tenant_id == self.tenant_id and l.job_id == job_id
        ]
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    # ========================================
    # GESTION DES CONFLITS
    # ========================================

    def create_conflict(
        self,
        job_id: str,
        source_id: str,
        target_id: str,
        entity_type: EntityType,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        conflicting_fields: List[str]
    ) -> Conflict:
        """Crée un conflit à résoudre."""
        conflict = Conflict(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            job_id=job_id,
            source_id=source_id,
            target_id=target_id,
            entity_type=entity_type,
            source_data=source_data,
            target_data=target_data,
            conflicting_fields=conflicting_fields,
        )

        self._conflicts[conflict.id] = conflict
        return conflict

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: ConflictResolution,
        resolved_data: Optional[Dict[str, Any]] = None,
        resolved_by: Optional[str] = None
    ) -> Optional[Conflict]:
        """Résout un conflit."""
        conflict = self._conflicts.get(conflict_id)
        if not conflict or conflict.tenant_id != self.tenant_id:
            return None

        conflict.resolution = resolution
        conflict.resolved_at = datetime.now()
        conflict.resolved_by = resolved_by

        if resolution == ConflictResolution.SOURCE_WINS:
            conflict.resolved_data = conflict.source_data
        elif resolution == ConflictResolution.TARGET_WINS:
            conflict.resolved_data = conflict.target_data
        elif resolution == ConflictResolution.MERGE and resolved_data:
            conflict.resolved_data = resolved_data
        elif resolution == ConflictResolution.MANUAL and resolved_data:
            conflict.resolved_data = resolved_data

        return conflict

    def list_conflicts(
        self,
        job_id: Optional[str] = None,
        resolved: Optional[bool] = None
    ) -> List[Conflict]:
        """Liste les conflits."""
        conflicts = [
            c for c in self._conflicts.values()
            if c.tenant_id == self.tenant_id
        ]

        if job_id:
            conflicts = [c for c in conflicts if c.job_id == job_id]
        if resolved is not None:
            if resolved:
                conflicts = [c for c in conflicts if c.resolved_at is not None]
            else:
                conflicts = [c for c in conflicts if c.resolved_at is None]

        return sorted(conflicts, key=lambda x: x.created_at, reverse=True)

    # ========================================
    # STATISTIQUES
    # ========================================

    def get_connection_stats(self, connection_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'une connexion."""
        jobs = [j for j in self._sync_jobs.values() if j.connection_id == connection_id]

        total_syncs = len(jobs)
        successful = len([j for j in jobs if j.status == SyncStatus.COMPLETED])
        failed = len([j for j in jobs if j.status == SyncStatus.FAILED])
        partial = len([j for j in jobs if j.status == SyncStatus.PARTIAL])

        total_records = sum(j.total_records for j in jobs)
        created = sum(j.created_records for j in jobs)
        updated = sum(j.updated_records for j in jobs)

        health = self._health_checks.get(connection_id)

        return {
            "total_syncs": total_syncs,
            "successful_syncs": successful,
            "failed_syncs": failed,
            "partial_syncs": partial,
            "total_records_processed": total_records,
            "total_records_created": created,
            "total_records_updated": updated,
            "is_healthy": health.is_healthy if health else None,
            "last_sync_at": max((j.last_sync_at for j in jobs if j.last_sync_at), default=None),
        }


# ============================================================
# FACTORY
# ============================================================

def create_integration_service(tenant_id: str) -> IntegrationService:
    """Crée une instance du service Integration."""
    return IntegrationService(tenant_id=tenant_id)
