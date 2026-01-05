"""
AZALS MODULE T5 - Modèles Packs Pays
=====================================

Modèles SQLAlchemy pour les configurations par pays.
"""

from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Float, Enum, JSON, Date, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class TaxType(str, PyEnum):
    """Types de taxes."""
    VAT = "VAT"                    # TVA/VAT
    SALES_TAX = "SALES_TAX"        # Taxe sur les ventes
    CORPORATE_TAX = "CORPORATE_TAX"  # Impôt sur les sociétés
    PAYROLL_TAX = "PAYROLL_TAX"    # Charges sociales
    WITHHOLDING = "WITHHOLDING"    # Retenue à la source
    CUSTOMS = "CUSTOMS"            # Droits de douane
    EXCISE = "EXCISE"              # Accises
    OTHER = "OTHER"                # Autres


class DocumentType(str, PyEnum):
    """Types de documents légaux."""
    INVOICE = "INVOICE"            # Facture
    CREDIT_NOTE = "CREDIT_NOTE"    # Avoir
    PURCHASE_ORDER = "PURCHASE_ORDER"  # Bon de commande
    DELIVERY_NOTE = "DELIVERY_NOTE"    # Bon de livraison
    PAYSLIP = "PAYSLIP"            # Bulletin de paie
    TAX_RETURN = "TAX_RETURN"      # Déclaration fiscale
    BALANCE_SHEET = "BALANCE_SHEET"    # Bilan
    INCOME_STATEMENT = "INCOME_STATEMENT"  # Compte de résultat
    CONTRACT = "CONTRACT"          # Contrat
    OTHER = "OTHER"


class BankFormat(str, PyEnum):
    """Formats bancaires."""
    SEPA = "SEPA"                  # SEPA Europe
    SWIFT = "SWIFT"                # International
    ACH = "ACH"                    # US ACH
    BACS = "BACS"                  # UK BACS
    CMI = "CMI"                    # Maroc CMI
    RTGS = "RTGS"                  # Real-Time Gross Settlement
    OTHER = "OTHER"


class DateFormatStyle(str, PyEnum):
    """Styles de format de date."""
    DMY = "DMY"      # 31/12/2024
    MDY = "MDY"      # 12/31/2024
    YMD = "YMD"      # 2024-12-31
    DDMMYYYY = "DDMMYYYY"  # 31/12/2024
    MMDDYYYY = "MMDDYYYY"  # 12/31/2024
    YYYYMMDD = "YYYYMMDD"  # 2024-12-31


class NumberFormatStyle(str, PyEnum):
    """Styles de format de nombre."""
    EU = "EU"        # 1 234,56 (espace + virgule)
    US = "US"        # 1,234.56 (virgule + point)
    CH = "CH"        # 1'234.56 (apostrophe + point)


class PackStatus(str, PyEnum):
    """Statut d'un pack pays."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


# ============================================================================
# MODÈLES
# ============================================================================

class CountryPack(Base):
    """Configuration d'un pack pays."""
    __tablename__ = "country_packs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    country_code = Column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    country_name = Column(String(100), nullable=False)
    country_name_local = Column(String(100))

    status = Column(Enum(PackStatus), default=PackStatus.ACTIVE, nullable=False)

    # Localisation de base
    default_language = Column(String(5), default="fr")  # ISO 639-1
    default_currency = Column(String(3), nullable=False)  # ISO 4217
    currency_symbol = Column(String(10))
    currency_position = Column(String(10), default="after")  # before/after

    # Formats
    date_format = Column(Enum(DateFormatStyle), default=DateFormatStyle.DMY)
    time_format = Column(String(20), default="HH:mm")  # 24h ou 12h
    number_format = Column(Enum(NumberFormatStyle), default=NumberFormatStyle.EU)
    decimal_separator = Column(String(1), default=",")
    thousands_separator = Column(String(1), default=" ")

    # Fuseau horaire
    timezone = Column(String(50), default="Europe/Paris")
    week_start = Column(Integer, default=1)  # 0=Dim, 1=Lun

    # Fiscalité
    fiscal_year_start_month = Column(Integer, default=1)  # 1-12
    fiscal_year_start_day = Column(Integer, default=1)    # 1-31
    default_vat_rate = Column(Float, default=20.0)
    has_regional_taxes = Column(Boolean, default=False)

    # Légal
    company_id_label = Column(String(50), default="SIRET")  # SIRET, RC, NIF, etc.
    company_id_format = Column(String(100))  # Regex format
    vat_id_label = Column(String(50), default="TVA")
    vat_id_format = Column(String(100))  # Regex format

    # Configuration
    config = Column(JSON)  # Config additionnelle JSON

    # Métadonnées
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer)

    # Relations
    tax_rates = relationship("TaxRate", back_populates="country_pack", cascade="all, delete-orphan")
    document_templates = relationship("DocumentTemplate", back_populates="country_pack", cascade="all, delete-orphan")
    bank_configs = relationship("BankConfig", back_populates="country_pack", cascade="all, delete-orphan")
    holidays = relationship("PublicHoliday", back_populates="country_pack", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_country_pack_tenant_country", "tenant_id", "country_code", unique=True),
    )


class TaxRate(Base):
    """Taux de taxe par pays."""
    __tablename__ = "country_tax_rates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    country_pack_id = Column(Integer, ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    tax_type = Column(Enum(TaxType), nullable=False)
    code = Column(String(20), nullable=False)  # TVA_20, TVA_10, IS, etc.
    name = Column(String(100), nullable=False)
    description = Column(Text)

    rate = Column(Float, nullable=False)  # Pourcentage (20.0 = 20%)
    is_percentage = Column(Boolean, default=True)  # True=%, False=montant fixe

    # Applicabilité
    applies_to = Column(String(50))  # goods, services, both
    region = Column(String(100))  # Région si taxe régionale

    # Comptes comptables
    account_collected = Column(String(20))  # 44571 en France
    account_deductible = Column(String(20))  # 44566 en France
    account_payable = Column(String(20))     # 44551 en France

    # Dates de validité
    valid_from = Column(Date, default=date.today)
    valid_to = Column(Date)

    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    country_pack = relationship("CountryPack", back_populates="tax_rates")

    __table_args__ = (
        Index("idx_tax_rate_tenant_code", "tenant_id", "code"),
        Index("idx_tax_rate_country", "country_pack_id"),
    )


class DocumentTemplate(Base):
    """Templates de documents légaux par pays."""
    __tablename__ = "country_document_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    country_pack_id = Column(Integer, ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    document_type = Column(Enum(DocumentType), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Template
    template_format = Column(String(20), default="html")  # html, pdf, docx
    template_content = Column(Text)  # Contenu ou chemin
    template_path = Column(String(500))

    # Mentions légales obligatoires
    mandatory_fields = Column(JSON)  # Liste des champs obligatoires
    legal_mentions = Column(Text)    # Mentions légales à inclure

    # Numérotation
    numbering_prefix = Column(String(20))
    numbering_pattern = Column(String(50))  # FA-{YYYY}-{SEQ:6}
    numbering_reset = Column(String(20), default="yearly")  # yearly, monthly, never

    language = Column(String(5), default="fr")
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer)

    country_pack = relationship("CountryPack", back_populates="document_templates")

    __table_args__ = (
        Index("idx_doc_template_tenant_type", "tenant_id", "document_type"),
        Index("idx_doc_template_country", "country_pack_id"),
    )


class BankConfig(Base):
    """Configuration bancaire par pays."""
    __tablename__ = "country_bank_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    country_pack_id = Column(Integer, ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    bank_format = Column(Enum(BankFormat), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Format IBAN/BIC
    iban_prefix = Column(String(2))  # FR, MA, etc.
    iban_length = Column(Integer)
    bic_required = Column(Boolean, default=True)

    # Format fichier
    export_format = Column(String(20))  # xml, csv, txt
    export_encoding = Column(String(20), default="utf-8")
    export_template = Column(Text)  # Template de fichier

    # Spécificités
    config = Column(JSON)  # Config additionnelle

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    country_pack = relationship("CountryPack", back_populates="bank_configs")

    __table_args__ = (
        Index("idx_bank_config_tenant", "tenant_id", "bank_format"),
        Index("idx_bank_config_country", "country_pack_id"),
    )


class PublicHoliday(Base):
    """Jours fériés par pays."""
    __tablename__ = "country_public_holidays"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    country_pack_id = Column(Integer, ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(200), nullable=False)
    name_local = Column(String(200))

    # Date
    holiday_date = Column(Date)  # Date fixe
    month = Column(Integer)      # 1-12 si récurrent
    day = Column(Integer)        # 1-31 si récurrent
    is_fixed = Column(Boolean, default=True)  # True=fixe, False=mobile (Pâques, etc.)
    calculation_rule = Column(String(100))  # Règle pour jours mobiles

    # Applicabilité
    year = Column(Integer)  # Si spécifique à une année
    region = Column(String(100))  # Si régional
    is_national = Column(Boolean, default=True)

    # Impact
    is_work_day = Column(Boolean, default=False)
    affects_banks = Column(Boolean, default=True)
    affects_business = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    country_pack = relationship("CountryPack", back_populates="holidays")

    __table_args__ = (
        Index("idx_holiday_tenant_date", "tenant_id", "holiday_date"),
        Index("idx_holiday_country", "country_pack_id"),
    )


class LegalRequirement(Base):
    """Exigences légales par pays."""
    __tablename__ = "country_legal_requirements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    country_pack_id = Column(Integer, ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    category = Column(String(50), nullable=False)  # fiscal, social, commercial
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Obligation
    requirement_type = Column(String(50))  # declaration, payment, report
    frequency = Column(String(20))  # monthly, quarterly, yearly
    deadline_rule = Column(String(100))  # Règle de calcul échéance

    # Configuration
    config = Column(JSON)

    # Références légales
    legal_reference = Column(String(200))
    effective_date = Column(Date)
    end_date = Column(Date)

    is_mandatory = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_legal_req_tenant_cat", "tenant_id", "category"),
        Index("idx_legal_req_country", "country_pack_id"),
    )


class TenantCountrySettings(Base):
    """Paramètres pays activés pour un tenant."""
    __tablename__ = "tenant_country_settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    country_pack_id = Column(Integer, ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    is_primary = Column(Boolean, default=False)  # Pays principal
    is_active = Column(Boolean, default=True)

    # Overrides locaux
    custom_currency = Column(String(3))
    custom_language = Column(String(5))
    custom_timezone = Column(String(50))
    custom_config = Column(JSON)

    activated_at = Column(DateTime, default=datetime.utcnow)
    activated_by = Column(Integer)

    __table_args__ = (
        Index("idx_tenant_country_tenant", "tenant_id"),
        Index("idx_tenant_country_pack", "country_pack_id"),
    )
