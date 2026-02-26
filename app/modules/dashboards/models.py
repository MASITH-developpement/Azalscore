"""
AZALSCORE ERP - Module DASHBOARDS
==================================
Modeles SQLAlchemy pour tableaux de bord personnalisables.

Inspire de: Sage BI, Axonaut Analytics, Pennylane Dashboard,
Odoo Dashboard, Microsoft Power BI

Fonctionnalites:
- Dashboards personnalisables par utilisateur
- Widgets configurables (KPI, graphiques, listes)
- Sources de donnees multiples
- Filtres globaux (periode, entite)
- Mise en page drag & drop
- Partage de dashboards
- Rafraichissement automatique
- Export PDF/image
- Dashboards par role
- Alertes sur seuils
- Favoris et accueil
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
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

from app.core.types import UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class DashboardType(str, enum.Enum):
    """Types de tableaux de bord."""
    EXECUTIVE = "executive"          # Direction generale
    OPERATIONAL = "operational"      # Operationnel
    ANALYTICAL = "analytical"        # Analytique
    STRATEGIC = "strategic"          # Strategique
    TACTICAL = "tactical"            # Tactique
    SALES = "sales"                  # Commercial
    FINANCE = "finance"              # Finance
    HR = "hr"                        # Ressources humaines
    PRODUCTION = "production"        # Production
    INVENTORY = "inventory"          # Stock
    PROJECT = "project"              # Projets
    CUSTOMER = "customer"            # Clients
    CUSTOM = "custom"                # Personnalise


class WidgetType(str, enum.Enum):
    """Types de widgets."""
    KPI = "kpi"                      # Indicateur KPI simple
    KPI_CARD = "kpi_card"            # Carte KPI avec tendance
    CHART = "chart"                  # Graphique
    TABLE = "table"                  # Tableau de donnees
    LIST = "list"                    # Liste d'elements
    MAP = "map"                      # Carte geographique
    GAUGE = "gauge"                  # Jauge circulaire
    PROGRESS = "progress"            # Barre de progression
    TEXT = "text"                    # Texte/Markdown
    HTML = "html"                    # Contenu HTML
    IMAGE = "image"                  # Image
    IFRAME = "iframe"                # Contenu externe
    FILTER = "filter"                # Filtre global
    CALENDAR = "calendar"            # Calendrier
    TIMELINE = "timeline"            # Chronologie
    COUNTER = "counter"              # Compteur anime
    SPARKLINE = "sparkline"          # Mini graphique
    HEATMAP = "heatmap"              # Carte de chaleur
    PIVOT = "pivot"                  # Tableau croise dynamique
    TREE = "tree"                    # Arborescence
    FUNNEL = "funnel"                # Entonnoir
    SANKEY = "sankey"                # Diagramme de flux


class ChartType(str, enum.Enum):
    """Types de graphiques."""
    LINE = "line"                    # Courbe
    AREA = "area"                    # Aire
    STACKED_AREA = "stacked_area"    # Aire empilee
    BAR = "bar"                      # Barres verticales
    HORIZONTAL_BAR = "horizontal_bar"  # Barres horizontales
    STACKED_BAR = "stacked_bar"      # Barres empilees
    PIE = "pie"                      # Camembert
    DONUT = "donut"                  # Anneau
    SCATTER = "scatter"              # Nuage de points
    BUBBLE = "bubble"                # Bulles
    RADAR = "radar"                  # Radar
    POLAR = "polar"                  # Polaire
    TREEMAP = "treemap"              # Treemap
    WATERFALL = "waterfall"          # Cascade
    COMBO = "combo"                  # Combine (barres + lignes)
    CANDLESTICK = "candlestick"      # Chandelier (finance)
    HISTOGRAM = "histogram"          # Histogramme
    BOX_PLOT = "box_plot"            # Boite a moustaches


class DataSourceType(str, enum.Enum):
    """Types de sources de donnees."""
    INTERNAL = "internal"            # Module interne AZALSCORE
    DATABASE = "database"            # Base de donnees externe
    API = "api"                      # API externe
    FILE = "file"                    # Fichier (CSV, Excel)
    MANUAL = "manual"                # Saisie manuelle
    CALCULATED = "calculated"        # Calcule/formule
    AGGREGATED = "aggregated"        # Agregation de sources


class RefreshFrequency(str, enum.Enum):
    """Frequences de rafraichissement."""
    REALTIME = "realtime"            # Temps reel (websocket)
    SECONDS_10 = "seconds_10"        # 10 secondes
    SECONDS_30 = "seconds_30"        # 30 secondes
    MINUTE_1 = "minute_1"            # 1 minute
    MINUTE_5 = "minute_5"            # 5 minutes
    MINUTE_15 = "minute_15"          # 15 minutes
    MINUTE_30 = "minute_30"          # 30 minutes
    HOURLY = "hourly"                # Horaire
    DAILY = "daily"                  # Quotidien
    WEEKLY = "weekly"                # Hebdomadaire
    ON_DEMAND = "on_demand"          # A la demande


class AlertSeverity(str, enum.Enum):
    """Severite des alertes."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Statut des alertes."""
    ACTIVE = "active"                # Active
    ACKNOWLEDGED = "acknowledged"    # Acquittee
    RESOLVED = "resolved"            # Resolue
    SNOOZED = "snoozed"              # En pause
    EXPIRED = "expired"              # Expiree


class AlertOperator(str, enum.Enum):
    """Operateurs pour conditions d'alerte."""
    EQ = "eq"                        # Egal
    NE = "ne"                        # Different
    GT = "gt"                        # Superieur
    GTE = "gte"                      # Superieur ou egal
    LT = "lt"                        # Inferieur
    LTE = "lte"                      # Inferieur ou egal
    BETWEEN = "between"              # Entre
    CONTAINS = "contains"            # Contient
    NOT_CONTAINS = "not_contains"    # Ne contient pas
    IS_NULL = "is_null"              # Est null
    IS_NOT_NULL = "is_not_null"      # N'est pas null
    CHANGE_PCT = "change_pct"        # Variation en %
    CHANGE_ABS = "change_abs"        # Variation absolue


class SharePermission(str, enum.Enum):
    """Permissions de partage."""
    VIEW = "view"                    # Lecture seule
    INTERACT = "interact"            # Interaction (filtres)
    EDIT = "edit"                    # Modification
    MANAGE = "manage"                # Gestion complete


class ExportFormat(str, enum.Enum):
    """Formats d'export."""
    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"
    SVG = "svg"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ExportStatus(str, enum.Enum):
    """Statuts d'export."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


# ============================================================================
# MODELS - DASHBOARD
# ============================================================================

class Dashboard(Base):
    """Tableau de bord personnalisable."""
    __tablename__ = "dash_dashboards"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_dash_dashboard_code"),
        Index("ix_dash_dashboards_tenant", "tenant_id"),
        Index("ix_dash_dashboards_owner", "tenant_id", "owner_id"),
        Index("ix_dash_dashboards_type", "tenant_id", "dashboard_type"),
        Index("ix_dash_dashboards_active", "tenant_id", "is_active", "deleted_at"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icone du dashboard
    color = Column(String(20), nullable=True)  # Couleur du dashboard
    dashboard_type = Column(Enum(DashboardType), default=DashboardType.CUSTOM)

    # Proprietaire et partage
    owner_id = Column(UniversalUUID(), nullable=False)
    is_shared = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)  # Public pour tout le tenant
    is_template = Column(Boolean, default=False)  # Template reutilisable
    shared_with_users = Column(JSON, nullable=True)  # [{user_id, permission}]
    shared_with_roles = Column(JSON, nullable=True)  # [{role, permission}]
    shared_with_teams = Column(JSON, nullable=True)  # [{team_id, permission}]

    # Configuration mise en page
    layout_type = Column(String(20), default="grid")  # grid, flex, tabs
    layout_config = Column(JSON, nullable=True)  # Configuration grille
    columns = Column(Integer, default=12)  # Nombre de colonnes grille
    row_height = Column(Integer, default=80)  # Hauteur ligne en pixels
    margin = Column(Integer, default=10)  # Marge entre widgets
    is_compact = Column(Boolean, default=True)  # Compactage vertical
    is_draggable = Column(Boolean, default=True)  # Widgets deplacables
    is_resizable = Column(Boolean, default=True)  # Widgets redimensionnables

    # Theme et apparence
    theme = Column(String(50), default="default")
    background_color = Column(String(20), nullable=True)
    background_image = Column(String(500), nullable=True)
    custom_css = Column(Text, nullable=True)

    # Rafraichissement
    refresh_frequency = Column(Enum(RefreshFrequency), default=RefreshFrequency.ON_DEMAND)
    auto_refresh = Column(Boolean, default=False)
    last_refreshed_at = Column(DateTime, nullable=True)

    # Filtres globaux
    global_filters = Column(JSON, nullable=True)  # Definition des filtres
    default_filters = Column(JSON, nullable=True)  # Valeurs par defaut
    default_date_range = Column(String(50), nullable=True)  # last_7_days, last_month...
    date_range_field = Column(String(100), nullable=True)  # Champ date pour filtres

    # Favoris et accueil
    is_default = Column(Boolean, default=False)  # Dashboard par defaut user
    is_home = Column(Boolean, default=False)  # Page d'accueil
    is_pinned = Column(Boolean, default=False)  # Epingle
    display_order = Column(Integer, default=0)

    # Tags et categories
    tags = Column(JSON, nullable=True)  # ["finance", "mensuel"]
    category = Column(String(100), nullable=True)

    # Statistiques
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime, nullable=True)
    last_viewed_by = Column(UniversalUUID(), nullable=True)

    # Metadonnees
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_by = Column(UniversalUUID(), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Relations
    widgets = relationship("DashboardWidget", back_populates="dashboard",
                          cascade="all, delete-orphan", lazy="selectin")
    shares = relationship("DashboardShare", back_populates="dashboard",
                         cascade="all, delete-orphan")
    favorites = relationship("DashboardFavorite", back_populates="dashboard",
                            cascade="all, delete-orphan")


class DashboardWidget(Base):
    """Widget d'un tableau de bord."""
    __tablename__ = "dash_widgets"
    __table_args__ = (
        Index("ix_dash_widgets_dashboard", "dashboard_id"),
        Index("ix_dash_widgets_tenant", "tenant_id"),
        Index("ix_dash_widgets_type", "tenant_id", "widget_type"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="CASCADE"), nullable=False)

    # Identification
    code = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)

    # Type
    widget_type = Column(Enum(WidgetType), nullable=False)
    chart_type = Column(Enum(ChartType), nullable=True)

    # Position et taille (grille)
    position_x = Column(Integer, default=0)  # Colonne
    position_y = Column(Integer, default=0)  # Ligne
    width = Column(Integer, default=4)  # Largeur en colonnes
    height = Column(Integer, default=3)  # Hauteur en lignes
    min_width = Column(Integer, default=2)
    min_height = Column(Integer, default=2)
    max_width = Column(Integer, nullable=True)
    max_height = Column(Integer, nullable=True)

    # Source de donnees
    data_source_id = Column(UniversalUUID(), ForeignKey("dash_data_sources.id"), nullable=True)
    query_config = Column(JSON, nullable=True)  # Configuration requete
    static_data = Column(JSON, nullable=True)  # Donnees statiques

    # Configuration specifique au type
    config = Column(JSON, nullable=True)  # Options widget
    chart_options = Column(JSON, nullable=True)  # Options graphique
    display_options = Column(JSON, nullable=True)  # Options affichage

    # Mapping donnees
    data_mapping = Column(JSON, nullable=True)  # {x_axis, y_axis, series...}
    aggregation = Column(JSON, nullable=True)  # {function, field, group_by}

    # Style
    colors = Column(JSON, nullable=True)  # Palette couleurs
    custom_style = Column(JSON, nullable=True)  # CSS custom

    # Interactions
    drill_down_config = Column(JSON, nullable=True)  # Config drill-down
    click_action = Column(JSON, nullable=True)  # Action au clic
    hover_action = Column(JSON, nullable=True)  # Action au survol
    links = Column(JSON, nullable=True)  # Liens contextuels

    # Filtres
    filters = Column(JSON, nullable=True)  # Filtres locaux widget
    linked_to_global = Column(Boolean, default=True)  # Lie aux filtres globaux
    filter_fields = Column(JSON, nullable=True)  # Champs filtres actifs

    # Rafraichissement
    refresh_frequency = Column(Enum(RefreshFrequency), nullable=True)
    last_refreshed_at = Column(DateTime, nullable=True)
    cache_ttl_seconds = Column(Integer, default=300)

    # Affichage
    show_title = Column(Boolean, default=True)
    show_subtitle = Column(Boolean, default=False)
    show_legend = Column(Boolean, default=True)
    show_toolbar = Column(Boolean, default=True)
    show_border = Column(Boolean, default=True)
    show_loading = Column(Boolean, default=True)

    # Alertes
    has_alerts = Column(Boolean, default=False)
    alert_config = Column(JSON, nullable=True)

    # Metadonnees
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    dashboard = relationship("Dashboard", back_populates="widgets")
    data_source = relationship("DataSource", foreign_keys=[data_source_id])


# ============================================================================
# MODELS - DATA SOURCES
# ============================================================================

class DataSource(Base):
    """Source de donnees pour widgets."""
    __tablename__ = "dash_data_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_dash_datasource_code"),
        Index("ix_dash_datasources_tenant", "tenant_id"),
        Index("ix_dash_datasources_type", "tenant_id", "source_type"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(Enum(DataSourceType), nullable=False)

    # Configuration source interne
    module = Column(String(100), nullable=True)  # Module AZALSCORE
    model = Column(String(100), nullable=True)  # Modele SQLAlchemy
    endpoint = Column(String(500), nullable=True)  # Endpoint API

    # Configuration externe
    connection_config = Column(JSON, nullable=True)
    # DATABASE: {host, port, database, username, password_encrypted, ssl}
    # API: {base_url, auth_type, api_key_encrypted, headers}
    # FILE: {file_path, file_type, delimiter}

    # Schema
    schema_definition = Column(JSON, nullable=True)  # Colonnes disponibles
    available_fields = Column(JSON, nullable=True)  # Champs selectionnables
    available_aggregations = Column(JSON, nullable=True)  # Agregations possibles
    available_filters = Column(JSON, nullable=True)  # Filtres possibles

    # Requete par defaut
    default_query = Column(JSON, nullable=True)
    default_filters = Column(JSON, nullable=True)
    default_sort = Column(JSON, nullable=True)
    default_limit = Column(Integer, default=1000)

    # Cache
    cache_enabled = Column(Boolean, default=True)
    cache_ttl_seconds = Column(Integer, default=300)
    last_cache_refresh = Column(DateTime, nullable=True)

    # Rafraichissement
    refresh_frequency = Column(Enum(RefreshFrequency), default=RefreshFrequency.ON_DEMAND)
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), nullable=True)
    sync_error = Column(Text, nullable=True)

    # Securite
    is_encrypted = Column(Boolean, default=True)
    allowed_roles = Column(JSON, nullable=True)
    row_level_security = Column(JSON, nullable=True)  # Filtres par role

    # Metadonnees
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class DataQuery(Base):
    """Requete de donnees sauvegardee."""
    __tablename__ = "dash_data_queries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_dash_query_code"),
        Index("ix_dash_queries_tenant", "tenant_id"),
        Index("ix_dash_queries_source", "data_source_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    data_source_id = Column(UniversalUUID(), ForeignKey("dash_data_sources.id"), nullable=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Type de requete
    query_type = Column(String(50), default="builder")  # builder, sql, api, aggregate

    # Configuration requete
    query_config = Column(JSON, nullable=True)  # Configuration builder
    # {select: [], filters: [], group_by: [], order_by: [], limit: N}

    raw_query = Column(Text, nullable=True)  # SQL brut si query_type=sql
    api_config = Column(JSON, nullable=True)  # Config API si query_type=api

    # Parametres
    parameters = Column(JSON, nullable=True)  # Parametres avec valeurs par defaut
    # [{name, type, default_value, required}]

    # Resultat
    result_columns = Column(JSON, nullable=True)  # Definition des colonnes
    sample_data = Column(JSON, nullable=True)  # Donnees d'exemple

    # Transformations
    transformations = Column(JSON, nullable=True)  # Transformations a appliquer
    # [{type: "rename", config: {...}}, {type: "calculate", config: {...}}]

    # Performance
    cache_enabled = Column(Boolean, default=False)
    cache_ttl_seconds = Column(Integer, default=300)
    last_executed_at = Column(DateTime, nullable=True)
    last_execution_time_ms = Column(Integer, nullable=True)
    avg_execution_time_ms = Column(Integer, nullable=True)
    execution_count = Column(Integer, default=0)

    # Securite
    allowed_roles = Column(JSON, nullable=True)

    # Metadonnees
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relations
    data_source = relationship("DataSource", foreign_keys=[data_source_id])


# ============================================================================
# MODELS - SHARING
# ============================================================================

class DashboardShare(Base):
    """Partage de dashboard."""
    __tablename__ = "dash_shares"
    __table_args__ = (
        Index("ix_dash_shares_dashboard", "dashboard_id"),
        Index("ix_dash_shares_tenant", "tenant_id"),
        Index("ix_dash_shares_user", "tenant_id", "shared_with_user_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="CASCADE"), nullable=False)

    # Type de partage
    share_type = Column(String(20), nullable=False)  # user, role, team, link

    # Destinataire
    shared_with_user_id = Column(UniversalUUID(), nullable=True)
    shared_with_role = Column(String(100), nullable=True)
    shared_with_team_id = Column(UniversalUUID(), nullable=True)

    # Lien public
    share_link = Column(String(100), nullable=True, unique=True)
    link_expires_at = Column(DateTime, nullable=True)
    link_password_hash = Column(String(255), nullable=True)
    link_access_count = Column(Integer, default=0)
    link_max_access = Column(Integer, nullable=True)

    # Permissions
    permission = Column(Enum(SharePermission), default=SharePermission.VIEW)
    can_export = Column(Boolean, default=True)
    can_share = Column(Boolean, default=False)

    # Notifications
    notify_on_share = Column(Boolean, default=True)
    notify_on_update = Column(Boolean, default=False)

    # Metadonnees
    shared_by = Column(UniversalUUID(), nullable=False)
    message = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)

    # Relations
    dashboard = relationship("Dashboard", back_populates="shares")


class DashboardFavorite(Base):
    """Favoris utilisateur."""
    __tablename__ = "dash_favorites"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "dashboard_id", name="uq_dash_favorite"),
        Index("ix_dash_favorites_user", "tenant_id", "user_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)
    dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="CASCADE"), nullable=False)

    # Organisation
    folder = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)

    # Personnalisation
    custom_name = Column(String(200), nullable=True)
    custom_icon = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Metadonnees
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    dashboard = relationship("Dashboard", back_populates="favorites")


# ============================================================================
# MODELS - ALERTS
# ============================================================================

class DashboardAlertRule(Base):
    """Regle d'alerte sur widget."""
    __tablename__ = "dash_alert_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_dash_alert_rule_code"),
        Index("ix_dash_alert_rules_tenant", "tenant_id"),
        Index("ix_dash_alert_rules_widget", "widget_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    widget_id = Column(UniversalUUID(), ForeignKey("dash_widgets.id", ondelete="CASCADE"), nullable=True)
    dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="CASCADE"), nullable=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING)

    # Condition
    metric_field = Column(String(200), nullable=False)  # Champ a surveiller
    operator = Column(Enum(AlertOperator), nullable=False)
    threshold_value = Column(Numeric(20, 4), nullable=True)
    threshold_value_2 = Column(Numeric(20, 4), nullable=True)  # Pour BETWEEN
    comparison_period = Column(String(50), nullable=True)  # Pour variations

    # Condition complexe (JSON pour conditions multiples)
    complex_condition = Column(JSON, nullable=True)
    # {type: "and"/"or", conditions: [{field, operator, value}]}

    # Frequence de verification
    check_frequency = Column(Enum(RefreshFrequency), default=RefreshFrequency.MINUTE_15)
    last_checked_at = Column(DateTime, nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)

    # Notifications
    notification_channels = Column(JSON, nullable=True)  # ["email", "sms", "push", "webhook"]
    recipients = Column(JSON, nullable=True)  # [{type: "user", id}, {type: "email", value}]
    cooldown_minutes = Column(Integer, default=60)  # Delai entre 2 alertes
    max_triggers_per_day = Column(Integer, nullable=True)

    # Message
    message_template = Column(Text, nullable=True)
    include_data = Column(Boolean, default=True)
    include_link = Column(Boolean, default=True)

    # Actions automatiques
    auto_resolve = Column(Boolean, default=False)
    auto_resolve_condition = Column(JSON, nullable=True)
    auto_actions = Column(JSON, nullable=True)  # Actions automatiques

    # Statut
    is_enabled = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Metadonnees
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class DashboardAlert(Base):
    """Alerte declenchee."""
    __tablename__ = "dash_alerts"
    __table_args__ = (
        Index("ix_dash_alerts_tenant", "tenant_id"),
        Index("ix_dash_alerts_rule", "rule_id"),
        Index("ix_dash_alerts_status", "tenant_id", "status"),
        Index("ix_dash_alerts_date", "tenant_id", "triggered_at"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    rule_id = Column(UniversalUUID(), ForeignKey("dash_alert_rules.id", ondelete="SET NULL"), nullable=True)
    widget_id = Column(UniversalUUID(), ForeignKey("dash_widgets.id", ondelete="SET NULL"), nullable=True)
    dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="SET NULL"), nullable=True)

    # Alerte
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)

    # Valeurs
    metric_field = Column(String(200), nullable=True)
    current_value = Column(Numeric(20, 4), nullable=True)
    threshold_value = Column(Numeric(20, 4), nullable=True)
    previous_value = Column(Numeric(20, 4), nullable=True)
    change_percentage = Column(Numeric(10, 2), nullable=True)

    # Contexte
    context_data = Column(JSON, nullable=True)
    link = Column(String(500), nullable=True)
    screenshot_url = Column(String(500), nullable=True)

    # Gestion
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(UniversalUUID(), nullable=True)
    acknowledged_notes = Column(Text, nullable=True)

    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UniversalUUID(), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_type = Column(String(50), nullable=True)  # manual, auto, timeout

    # Snooze
    snoozed_until = Column(DateTime, nullable=True)
    snoozed_by = Column(UniversalUUID(), nullable=True)

    # Notifications envoyees
    notifications_sent = Column(JSON, nullable=True)
    # [{channel, recipient, sent_at, status}]

    # Metadonnees
    triggered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# MODELS - EXPORTS
# ============================================================================

class DashboardExport(Base):
    """Historique des exports."""
    __tablename__ = "dash_exports"
    __table_args__ = (
        Index("ix_dash_exports_tenant", "tenant_id"),
        Index("ix_dash_exports_user", "tenant_id", "user_id"),
        Index("ix_dash_exports_date", "tenant_id", "created_at"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)
    dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="SET NULL"), nullable=True)
    widget_id = Column(UniversalUUID(), ForeignKey("dash_widgets.id", ondelete="SET NULL"), nullable=True)

    # Export
    export_type = Column(String(50), nullable=False)  # dashboard, widget, data
    export_format = Column(Enum(ExportFormat), nullable=False)
    status = Column(Enum(ExportStatus), default=ExportStatus.PENDING)

    # Configuration
    export_config = Column(JSON, nullable=True)
    # {page_size, orientation, include_header, filters_applied, date_range}

    # Filtres appliques
    filters_applied = Column(JSON, nullable=True)
    date_range_applied = Column(JSON, nullable=True)

    # Fichier
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_expires_at = Column(DateTime, nullable=True)

    # Execution
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadonnees
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# MODELS - SCHEDULED REPORTS
# ============================================================================

class ScheduledReport(Base):
    """Rapport planifie."""
    __tablename__ = "dash_scheduled_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_dash_scheduled_report_code"),
        Index("ix_dash_scheduled_tenant", "tenant_id"),
        Index("ix_dash_scheduled_next", "next_run_at"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="CASCADE"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Planification
    cron_expression = Column(String(100), nullable=True)  # Expression cron
    frequency = Column(Enum(RefreshFrequency), nullable=True)  # Alternative simple
    timezone = Column(String(50), default="Europe/Paris")

    # Execution
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(Enum(ExportStatus), nullable=True)
    last_error = Column(Text, nullable=True)
    run_count = Column(Integer, default=0)

    # Format export
    export_format = Column(Enum(ExportFormat), default=ExportFormat.PDF)
    export_config = Column(JSON, nullable=True)

    # Filtres
    filters = Column(JSON, nullable=True)
    date_range_type = Column(String(50), nullable=True)  # last_day, last_week, last_month

    # Distribution
    distribution_method = Column(String(50), default="email")  # email, storage, webhook
    recipients = Column(JSON, nullable=True)
    # [{type: "email", value: "..."}, {type: "user", id: "..."}]

    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)

    webhook_url = Column(String(500), nullable=True)
    storage_path = Column(String(500), nullable=True)

    # Options
    include_summary = Column(Boolean, default=True)
    attach_data = Column(Boolean, default=False)

    # Statut
    is_enabled = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Metadonnees
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    deleted_at = Column(DateTime, nullable=True)


# ============================================================================
# MODELS - USER PREFERENCES
# ============================================================================

class UserDashboardPreference(Base):
    """Preferences utilisateur pour dashboards."""
    __tablename__ = "dash_user_preferences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_dash_user_pref"),
        Index("ix_dash_user_pref_tenant", "tenant_id"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False)

    # Dashboard par defaut
    default_dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="SET NULL"), nullable=True)
    home_dashboard_id = Column(UniversalUUID(), ForeignKey("dash_dashboards.id", ondelete="SET NULL"), nullable=True)

    # Preferences globales
    theme = Column(String(50), default="system")  # light, dark, system
    language = Column(String(10), default="fr")
    timezone = Column(String(50), default="Europe/Paris")
    date_format = Column(String(50), default="DD/MM/YYYY")
    number_format = Column(String(50), default="fr-FR")

    # Preferences affichage
    default_date_range = Column(String(50), default="last_30_days")
    auto_refresh_enabled = Column(Boolean, default=True)
    compact_mode = Column(Boolean, default=False)
    show_tooltips = Column(Boolean, default=True)
    animation_enabled = Column(Boolean, default=True)

    # Notifications
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    notification_frequency = Column(String(50), default="immediate")

    # Historique recent
    recent_dashboards = Column(JSON, nullable=True)  # [dashboard_id, ...]
    recent_filters = Column(JSON, nullable=True)
    saved_filters = Column(JSON, nullable=True)

    # Metadonnees
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# MODELS - DASHBOARD TEMPLATES
# ============================================================================

class DashboardTemplate(Base):
    """Template de dashboard reutilisable."""
    __tablename__ = "dash_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_dash_template_code"),
        Index("ix_dash_templates_tenant", "tenant_id"),
        Index("ix_dash_templates_type", "tenant_id", "dashboard_type"),
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    preview_image = Column(String(500), nullable=True)
    dashboard_type = Column(Enum(DashboardType), default=DashboardType.CUSTOM)

    # Contenu
    layout_config = Column(JSON, nullable=False)  # Configuration complete
    widgets_config = Column(JSON, nullable=False)  # Configuration widgets
    theme_config = Column(JSON, nullable=True)  # Theme
    filters_config = Column(JSON, nullable=True)  # Filtres

    # Categories et tags
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)

    # Pour role
    target_roles = Column(JSON, nullable=True)  # Roles cibles

    # Statistiques
    usage_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), nullable=True)
    rating_count = Column(Integer, default=0)

    # Disponibilite
    is_public = Column(Boolean, default=False)  # Disponible pour tous tenants
    is_system = Column(Boolean, default=False)  # Template systeme
    is_active = Column(Boolean, default=True)

    # Metadonnees
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
