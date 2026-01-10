"""
AZALS - Module M10: BI & Reporting
Modèles SQLAlchemy pour Business Intelligence
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db import Base
from app.core.types import UniversalUUID

# ============================================================================
# ENUMS
# ============================================================================

class DashboardType(str, enum.Enum):
    """Types de tableaux de bord."""
    EXECUTIVE = "executive"          # Direction générale
    OPERATIONAL = "operational"      # Opérationnel
    ANALYTICAL = "analytical"        # Analytique
    STRATEGIC = "strategic"          # Stratégique
    TACTICAL = "tactical"            # Tactique
    CUSTOM = "custom"                # Personnalisé


class WidgetType(str, enum.Enum):
    """Types de widgets."""
    CHART = "chart"                  # Graphique
    TABLE = "table"                  # Tableau
    KPI = "kpi"                      # Indicateur KPI
    MAP = "map"                      # Carte géographique
    GAUGE = "gauge"                  # Jauge
    TEXT = "text"                    # Texte/Markdown
    IMAGE = "image"                  # Image
    IFRAME = "iframe"                # Contenu externe
    FILTER = "filter"                # Filtre global
    LIST = "list"                    # Liste d'éléments


class ChartType(str, enum.Enum):
    """Types de graphiques."""
    LINE = "line"                    # Courbe
    BAR = "bar"                      # Barres verticales
    HORIZONTAL_BAR = "horizontal_bar"  # Barres horizontales
    PIE = "pie"                      # Camembert
    DONUT = "donut"                  # Anneau
    AREA = "area"                    # Aire
    SCATTER = "scatter"              # Nuage de points
    BUBBLE = "bubble"                # Bulles
    RADAR = "radar"                  # Radar
    HEATMAP = "heatmap"              # Carte de chaleur
    TREEMAP = "treemap"              # Treemap
    FUNNEL = "funnel"                # Entonnoir
    WATERFALL = "waterfall"          # Cascade
    COMBO = "combo"                  # Combiné


class ReportType(str, enum.Enum):
    """Types de rapports."""
    FINANCIAL = "financial"          # Financier
    SALES = "sales"                  # Ventes
    HR = "hr"                        # Ressources humaines
    PRODUCTION = "production"        # Production
    INVENTORY = "inventory"          # Stock
    QUALITY = "quality"              # Qualité
    MAINTENANCE = "maintenance"      # Maintenance
    PROJECT = "project"              # Projets
    CUSTOM = "custom"                # Personnalisé
    REGULATORY = "regulatory"        # Réglementaire
    AUDIT = "audit"                  # Audit


class ReportFormat(str, enum.Enum):
    """Formats d'export."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    XML = "xml"


class ReportStatus(str, enum.Enum):
    """Statuts d'exécution de rapport."""
    PENDING = "pending"              # En attente
    RUNNING = "running"              # En cours
    COMPLETED = "completed"          # Terminé
    FAILED = "failed"                # Échoué
    CANCELLED = "cancelled"          # Annulé


class KPICategory(str, enum.Enum):
    """Catégories de KPIs."""
    FINANCIAL = "financial"          # Financier
    COMMERCIAL = "commercial"        # Commercial
    OPERATIONAL = "operational"      # Opérationnel
    HR = "hr"                        # RH
    QUALITY = "quality"              # Qualité
    CUSTOMER = "customer"            # Client
    PROCESS = "process"              # Processus
    INNOVATION = "innovation"        # Innovation


class KPITrend(str, enum.Enum):
    """Tendance des KPIs."""
    UP = "up"                        # En hausse
    DOWN = "down"                    # En baisse
    STABLE = "stable"                # Stable
    UNKNOWN = "unknown"              # Inconnu


class AlertSeverity(str, enum.Enum):
    """Sévérité des alertes."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Statut des alertes."""
    ACTIVE = "active"                # Active
    ACKNOWLEDGED = "acknowledged"    # Acquittée
    RESOLVED = "resolved"            # Résolue
    SNOOZED = "snoozed"              # En pause


class DataSourceType(str, enum.Enum):
    """Types de sources de données."""
    DATABASE = "database"            # Base interne
    API = "api"                      # API externe
    FILE = "file"                    # Fichier
    MANUAL = "manual"                # Saisie manuelle


class RefreshFrequency(str, enum.Enum):
    """Fréquences de rafraîchissement."""
    REALTIME = "realtime"            # Temps réel
    MINUTE_1 = "minute_1"            # Chaque minute
    MINUTE_5 = "minute_5"            # Toutes les 5 minutes
    MINUTE_15 = "minute_15"          # Toutes les 15 minutes
    MINUTE_30 = "minute_30"          # Toutes les 30 minutes
    HOURLY = "hourly"                # Horaire
    DAILY = "daily"                  # Quotidien
    WEEKLY = "weekly"                # Hebdomadaire
    MONTHLY = "monthly"              # Mensuel
    ON_DEMAND = "on_demand"          # À la demande


# ============================================================================
# MODELS - DASHBOARDS
# ============================================================================

class Dashboard(Base):
    """Tableau de bord."""
    __tablename__ = "bi_dashboards"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_bi_dashboard_code"),
        Index("ix_bi_dashboards_tenant", "tenant_id"),
        Index("ix_bi_dashboards_owner", "tenant_id", "owner_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    dashboard_type = Column(Enum(DashboardType), default=DashboardType.CUSTOM)

    # Propriétaire
    owner_id = Column(UniversalUUID(), nullable=False)
    is_shared = Column(Boolean, default=False)
    shared_with = Column(JSON, nullable=True)  # Liste d'IDs utilisateurs/rôles

    # Configuration
    layout = Column(JSON, nullable=True)  # Configuration de la grille
    theme = Column(String(50), default="default")
    refresh_frequency = Column(Enum(RefreshFrequency), default=RefreshFrequency.ON_DEMAND)
    auto_refresh = Column(Boolean, default=False)

    # Filtres globaux
    global_filters = Column(JSON, nullable=True)
    default_date_range = Column(String(50), nullable=True)  # last_7_days, last_month, etc.

    # Favoris et accès
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime, nullable=True)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardWidget(Base):
    """Widget d'un tableau de bord."""
    __tablename__ = "bi_dashboard_widgets"
    __table_args__ = (
        Index("ix_bi_widgets_dashboard", "dashboard_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    dashboard_id = Column(UniversalUUID(), ForeignKey("bi_dashboards.id", ondelete="CASCADE"), nullable=False)

    # Identification
    title = Column(String(200), nullable=False)
    widget_type = Column(Enum(WidgetType), nullable=False)
    chart_type = Column(Enum(ChartType), nullable=True)

    # Position et taille (grille)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)  # Colonnes (sur 12)
    height = Column(Integer, default=3)  # Unités

    # Source de données
    data_source_id = Column(UniversalUUID(), ForeignKey("bi_data_sources.id"), nullable=True)
    query_id = Column(UniversalUUID(), ForeignKey("bi_data_queries.id"), nullable=True)
    kpi_id = Column(UniversalUUID(), ForeignKey("bi_kpi_definitions.id"), nullable=True)

    # Configuration du widget
    config = Column(JSON, nullable=True)  # Options spécifiques au type
    chart_options = Column(JSON, nullable=True)  # Options du graphique
    colors = Column(JSON, nullable=True)  # Palette de couleurs

    # Données
    static_data = Column(JSON, nullable=True)  # Données statiques (pour type text, image)
    data_mapping = Column(JSON, nullable=True)  # Mapping des colonnes

    # Interactions
    drill_down_config = Column(JSON, nullable=True)
    click_action = Column(JSON, nullable=True)  # Action au clic

    # Affichage
    show_title = Column(Boolean, default=True)
    show_legend = Column(Boolean, default=True)
    show_toolbar = Column(Boolean, default=True)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    dashboard = relationship("Dashboard", back_populates="widgets")
    filters = relationship("WidgetFilter", back_populates="widget", cascade="all, delete-orphan")


class WidgetFilter(Base):
    """Filtre appliqué à un widget."""
    __tablename__ = "bi_widget_filters"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    widget_id = Column(UniversalUUID(), ForeignKey("bi_dashboard_widgets.id", ondelete="CASCADE"), nullable=False)

    # Définition du filtre
    field_name = Column(String(100), nullable=False)
    operator = Column(String(20), nullable=False)  # eq, ne, gt, lt, contains, etc.
    value = Column(JSON, nullable=True)
    is_dynamic = Column(Boolean, default=False)  # Lié à un filtre global

    # Métadonnées
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    widget = relationship("DashboardWidget", back_populates="filters")


# ============================================================================
# MODELS - REPORTS
# ============================================================================

class Report(Base):
    """Définition d'un rapport."""
    __tablename__ = "bi_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_bi_report_code"),
        Index("ix_bi_reports_tenant", "tenant_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)

    # Template
    template = Column(Text, nullable=True)  # Template HTML/Jinja
    template_file = Column(String(255), nullable=True)

    # Sources de données
    data_sources = Column(JSON, nullable=True)  # Liste des sources
    queries = Column(JSON, nullable=True)  # Requêtes associées
    parameters = Column(JSON, nullable=True)  # Paramètres du rapport

    # Formats disponibles
    available_formats = Column(JSON, default=["pdf", "excel"])
    default_format = Column(Enum(ReportFormat), default=ReportFormat.PDF)

    # Options
    page_size = Column(String(20), default="A4")
    orientation = Column(String(20), default="portrait")
    margins = Column(JSON, nullable=True)
    header_template = Column(Text, nullable=True)
    footer_template = Column(Text, nullable=True)

    # Accès
    owner_id = Column(UniversalUUID(), nullable=False)
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(JSON, nullable=True)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    schedules = relationship("ReportSchedule", back_populates="report", cascade="all, delete-orphan")
    executions = relationship("ReportExecution", back_populates="report", cascade="all, delete-orphan")


class ReportSchedule(Base):
    """Planification d'un rapport."""
    __tablename__ = "bi_report_schedules"
    __table_args__ = (
        Index("ix_bi_schedules_report", "report_id"),
        Index("ix_bi_schedules_next_run", "next_run_at"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    report_id = Column(UniversalUUID(), ForeignKey("bi_reports.id", ondelete="CASCADE"), nullable=False)

    # Planification
    name = Column(String(200), nullable=False)
    cron_expression = Column(String(100), nullable=True)  # Expression cron
    frequency = Column(Enum(RefreshFrequency), nullable=True)

    # Prochaine exécution
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(Enum(ReportStatus), nullable=True)

    # Paramètres
    parameters = Column(JSON, nullable=True)
    output_format = Column(Enum(ReportFormat), default=ReportFormat.PDF)

    # Distribution
    recipients = Column(JSON, nullable=True)  # Emails ou user_ids
    distribution_method = Column(String(50), default="email")  # email, storage, webhook

    # Options
    is_enabled = Column(Boolean, default=True)
    timezone = Column(String(50), default="Europe/Paris")

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    report = relationship("Report", back_populates="schedules")


class ReportExecution(Base):
    """Exécution d'un rapport."""
    __tablename__ = "bi_report_executions"
    __table_args__ = (
        Index("ix_bi_executions_report", "report_id"),
        Index("ix_bi_executions_status", "status"),
        Index("ix_bi_executions_date", "started_at"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    report_id = Column(UniversalUUID(), ForeignKey("bi_reports.id", ondelete="CASCADE"), nullable=False)
    schedule_id = Column(UniversalUUID(), ForeignKey("bi_report_schedules.id"), nullable=True)

    # Exécution
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Paramètres utilisés
    parameters = Column(JSON, nullable=True)
    output_format = Column(Enum(ReportFormat), nullable=False)

    # Résultat
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_url = Column(String(500), nullable=True)
    row_count = Column(Integer, nullable=True)

    # Erreur
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Métadonnées
    triggered_by = Column(UniversalUUID(), nullable=True)  # user_id ou null si planifié
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    report = relationship("Report", back_populates="executions")


# ============================================================================
# MODELS - KPIs
# ============================================================================

class KPIDefinition(Base):
    """Définition d'un KPI."""
    __tablename__ = "bi_kpi_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_bi_kpi_code"),
        Index("ix_bi_kpis_tenant", "tenant_id"),
        Index("ix_bi_kpis_category", "tenant_id", "category"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(KPICategory), nullable=False)

    # Calcul
    formula = Column(Text, nullable=True)  # Expression de calcul
    unit = Column(String(50), nullable=True)  # %, €, unités, etc.
    precision = Column(Integer, default=2)
    aggregation_method = Column(String(50), default="sum")  # sum, avg, count, max, min

    # Source de données
    data_source_id = Column(UniversalUUID(), ForeignKey("bi_data_sources.id"), nullable=True)
    query = Column(Text, nullable=True)

    # Affichage
    display_format = Column(String(50), nullable=True)  # currency, percentage, number
    good_threshold = Column(Numeric(15, 4), nullable=True)
    warning_threshold = Column(Numeric(15, 4), nullable=True)
    bad_threshold = Column(Numeric(15, 4), nullable=True)
    higher_is_better = Column(Boolean, default=True)

    # Fréquence de calcul
    refresh_frequency = Column(Enum(RefreshFrequency), default=RefreshFrequency.DAILY)
    last_calculated_at = Column(DateTime, nullable=True)

    # Comparaison
    compare_to_previous = Column(Boolean, default=True)
    comparison_period = Column(String(50), default="previous_period")  # previous_period, same_period_last_year

    # Métadonnées
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # KPI système non modifiable
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    values = relationship("KPIValue", back_populates="kpi", cascade="all, delete-orphan")
    targets = relationship("KPITarget", back_populates="kpi", cascade="all, delete-orphan")


class KPIValue(Base):
    """Valeur historique d'un KPI."""
    __tablename__ = "bi_kpi_values"
    __table_args__ = (
        Index("ix_bi_kpi_values_kpi", "kpi_id"),
        Index("ix_bi_kpi_values_date", "kpi_id", "period_date"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    kpi_id = Column(UniversalUUID(), ForeignKey("bi_kpi_definitions.id", ondelete="CASCADE"), nullable=False)

    # Période
    period_date = Column(Date, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly

    # Valeur
    value = Column(Numeric(20, 4), nullable=False)
    previous_value = Column(Numeric(20, 4), nullable=True)
    change_percentage = Column(Numeric(10, 2), nullable=True)
    trend = Column(Enum(KPITrend), default=KPITrend.UNKNOWN)

    # Contexte
    dimension = Column(String(100), nullable=True)  # Pour segmentation
    dimension_value = Column(String(100), nullable=True)
    extra_data = Column(JSON, nullable=True)

    # Métadonnées
    calculated_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50), default="calculated")  # calculated, manual, imported

    # Relations
    kpi = relationship("KPIDefinition", back_populates="values")


class KPITarget(Base):
    """Objectif d'un KPI."""
    __tablename__ = "bi_kpi_targets"
    __table_args__ = (
        Index("ix_bi_kpi_targets_kpi", "kpi_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    kpi_id = Column(UniversalUUID(), ForeignKey("bi_kpi_definitions.id", ondelete="CASCADE"), nullable=False)

    # Période
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)  # Null = objectif annuel
    quarter = Column(Integer, nullable=True)  # 1-4

    # Objectif
    target_value = Column(Numeric(20, 4), nullable=False)
    min_value = Column(Numeric(20, 4), nullable=True)
    max_value = Column(Numeric(20, 4), nullable=True)

    # Progression
    current_value = Column(Numeric(20, 4), nullable=True)
    achievement_percentage = Column(Numeric(10, 2), nullable=True)

    # Métadonnées
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    kpi = relationship("KPIDefinition", back_populates="targets")


# ============================================================================
# MODELS - ALERTS
# ============================================================================

class Alert(Base):
    """Alerte déclenchée."""
    __tablename__ = "bi_alerts"
    __table_args__ = (
        Index("ix_bi_alerts_tenant", "tenant_id"),
        Index("ix_bi_alerts_status", "tenant_id", "status"),
        Index("ix_bi_alerts_severity", "tenant_id", "severity"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    rule_id = Column(UniversalUUID(), ForeignKey("bi_alert_rules.id"), nullable=True)

    # Alerte
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)

    # Source
    source_type = Column(String(50), nullable=True)  # kpi, report, threshold, etc.
    source_id = Column(UniversalUUID(), nullable=True)
    source_value = Column(Numeric(20, 4), nullable=True)
    threshold_value = Column(Numeric(20, 4), nullable=True)

    # Contexte
    context = Column(JSON, nullable=True)
    link = Column(String(500), nullable=True)

    # Gestion
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(UniversalUUID(), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UniversalUUID(), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Snooze
    snoozed_until = Column(DateTime, nullable=True)

    # Notifications
    notifications_sent = Column(JSON, nullable=True)

    # Métadonnées
    triggered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertRule(Base):
    """Règle de déclenchement d'alerte."""
    __tablename__ = "bi_alert_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_bi_alert_rule_code"),
        Index("ix_bi_alert_rules_tenant", "tenant_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(AlertSeverity), nullable=False)

    # Condition
    source_type = Column(String(50), nullable=False)  # kpi, query, threshold
    source_id = Column(UniversalUUID(), nullable=True)
    condition = Column(JSON, nullable=False)  # {operator, value, field}

    # Exemple condition:
    # {"operator": "gt", "value": 100, "field": "total_sales"}
    # {"operator": "lt", "value": 10, "field": "stock_level"}

    # Fréquence
    check_frequency = Column(Enum(RefreshFrequency), default=RefreshFrequency.HOURLY)
    last_checked_at = Column(DateTime, nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)

    # Notifications
    notification_channels = Column(JSON, nullable=True)  # email, sms, webhook
    recipients = Column(JSON, nullable=True)
    cooldown_minutes = Column(Integer, default=60)  # Éviter spam

    # Options
    is_enabled = Column(Boolean, default=True)
    auto_resolve = Column(Boolean, default=False)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)


# ============================================================================
# MODELS - DATA SOURCES
# ============================================================================

class DataSource(Base):
    """Source de données pour BI."""
    __tablename__ = "bi_data_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_bi_datasource_code"),
        Index("ix_bi_datasources_tenant", "tenant_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(Enum(DataSourceType), nullable=False)

    # Configuration connexion
    connection_config = Column(JSON, nullable=True)
    # Pour DATABASE: {host, port, database, username, password_encrypted}
    # Pour API: {base_url, auth_type, api_key_encrypted}
    # Pour FILE: {file_path, file_type}

    # Schéma
    schema_definition = Column(JSON, nullable=True)  # Colonnes disponibles
    refresh_frequency = Column(Enum(RefreshFrequency), default=RefreshFrequency.DAILY)
    last_synced_at = Column(DateTime, nullable=True)

    # Cache
    cache_enabled = Column(Boolean, default=True)
    cache_ttl_seconds = Column(Integer, default=3600)

    # Sécurité
    is_encrypted = Column(Boolean, default=True)
    allowed_roles = Column(JSON, nullable=True)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)


class DataQuery(Base):
    """Requête de données réutilisable."""
    __tablename__ = "bi_data_queries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_bi_query_code"),
        Index("ix_bi_queries_tenant", "tenant_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    data_source_id = Column(UniversalUUID(), ForeignKey("bi_data_sources.id"), nullable=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Requête
    query_type = Column(String(50), default="sql")  # sql, api, aggregate
    query_text = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)  # Paramètres avec valeurs par défaut

    # Résultat
    result_columns = Column(JSON, nullable=True)  # Définition des colonnes
    sample_data = Column(JSON, nullable=True)  # Données d'exemple

    # Cache
    cache_enabled = Column(Boolean, default=False)
    cache_ttl_seconds = Column(Integer, default=300)
    last_executed_at = Column(DateTime, nullable=True)
    last_execution_time_ms = Column(Integer, nullable=True)

    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)


# ============================================================================
# MODELS - USER FEATURES
# ============================================================================

class Bookmark(Base):
    """Favoris utilisateur."""
    __tablename__ = "bi_bookmarks"
    __table_args__ = (
        Index("ix_bi_bookmarks_user", "tenant_id", "user_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)

    # Élément
    item_type = Column(String(50), nullable=False)  # dashboard, report, kpi
    item_id = Column(UniversalUUID(), nullable=False)
    item_name = Column(String(200), nullable=True)

    # Organisation
    folder = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportHistory(Base):
    """Historique des exports."""
    __tablename__ = "bi_export_history"
    __table_args__ = (
        Index("ix_bi_exports_user", "tenant_id", "user_id"),
        Index("ix_bi_exports_date", "created_at"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)

    # Export
    export_type = Column(String(50), nullable=False)  # dashboard, report, data
    item_type = Column(String(50), nullable=True)
    item_id = Column(UniversalUUID(), nullable=True)
    item_name = Column(String(200), nullable=True)

    # Format
    format = Column(Enum(ReportFormat), nullable=False)

    # Fichier
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_url = Column(String(500), nullable=True)

    # Statut
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    error_message = Column(Text, nullable=True)

    # Métadonnées
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
