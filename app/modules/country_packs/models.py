"""
AZALS MODULE T5 - Modèles Packs Pays
=====================================

Modèles SQLAlchemy pour les configurations par pays.
MIGRATED: All PKs and FKs use UUID for PostgreSQL compatibility.
"""

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean Date, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base
from app.core.types import UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    country_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    country_name_local: Mapped[Optional[str]] = mapped_column(String(100))

    status: Mapped[Optional[str]] = mapped_column(Enum(PackStatus), default=PackStatus.ACTIVE, nullable=False)

    # Localisation de base
    default_language: Mapped[Optional[str]] = mapped_column(String(5), default="fr")  # ISO 639-1
    default_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=False)  # ISO 4217
    currency_symbol: Mapped[Optional[str]] = mapped_column(String(10))
    currency_position: Mapped[Optional[str]] = mapped_column(String(10), default="after")  # before/after

    # Formats
    date_format: Mapped[Optional[str]] = mapped_column(Enum(DateFormatStyle), default=DateFormatStyle.DMY)
    time_format: Mapped[Optional[str]] = mapped_column(String(20), default="HH:mm")  # 24h ou 12h
    number_format: Mapped[Optional[str]] = mapped_column(Enum(NumberFormatStyle), default=NumberFormatStyle.EU)
    decimal_separator: Mapped[Optional[str]] = mapped_column(String(1), default=",")
    thousands_separator: Mapped[Optional[str]] = mapped_column(String(1), default=" ")

    # Fuseau horaire
    timezone: Mapped[Optional[str]] = mapped_column(String(50), default="Europe/Paris")
    week_start: Mapped[Optional[int]] = mapped_column(Integer, default=1)  # 0=Dim, 1=Lun

    # Fiscalité
    fiscal_year_start_month: Mapped[Optional[int]] = mapped_column(Integer, default=1)  # 1-12
    fiscal_year_start_day: Mapped[Optional[int]] = mapped_column(Integer, default=1)    # 1-31
    default_vat_rate: Mapped[Optional[float]] = mapped_column(Float, default=20.0)
    has_regional_taxes: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Légal
    company_id_label: Mapped[Optional[str]] = mapped_column(String(50), default="SIRET")  # SIRET, RC, NIF, etc.
    company_id_format: Mapped[Optional[str]] = mapped_column(String(100))  # Regex format
    vat_id_label: Mapped[Optional[str]] = mapped_column(String(50), default="TVA")
    vat_id_format: Mapped[Optional[str]] = mapped_column(String(100))  # Regex format

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON)  # Config additionnelle JSON

    # Métadonnées
    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

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

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    country_pack_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    tax_type: Mapped[Optional[str]] = mapped_column(Enum(TaxType), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=False)  # TVA_20, TVA_10, IS, etc.
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    rate: Mapped[float] = mapped_column(Float)  # Pourcentage (20.0 = 20%)
    is_percentage: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)  # True=%, False=montant fixe

    # Applicabilité
    applies_to: Mapped[Optional[str]] = mapped_column(String(50))  # goods, services, both
    region: Mapped[Optional[str]] = mapped_column(String(100))  # Région si taxe régionale

    # Comptes comptables
    account_collected: Mapped[Optional[str]] = mapped_column(String(20))  # 44571 en France
    account_deductible: Mapped[Optional[str]] = mapped_column(String(20))  # 44566 en France
    account_payable: Mapped[Optional[str]] = mapped_column(String(20))     # 44551 en France

    # Dates de validité
    valid_from: Mapped[Optional[date]] = mapped_column(Date, default=date.today)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    country_pack = relationship("CountryPack", back_populates="tax_rates")

    __table_args__ = (
        Index("idx_tax_rate_tenant_code", "tenant_id", "code"),
        Index("idx_tax_rate_country", "country_pack_id"),
    )


class DocumentTemplate(Base):
    """Templates de documents légaux par pays."""
    __tablename__ = "country_document_templates"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    country_pack_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    document_type: Mapped[Optional[str]] = mapped_column(Enum(DocumentType), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Template
    template_format: Mapped[Optional[str]] = mapped_column(String(20), default="html")  # html, pdf, docx
    template_content: Mapped[Optional[str]] = mapped_column(Text)  # Contenu ou chemin
    template_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Mentions légales obligatoires
    mandatory_fields: Mapped[Optional[dict]] = mapped_column(JSON)  # Liste des champs obligatoires
    legal_mentions: Mapped[Optional[str]] = mapped_column(Text)    # Mentions légales à inclure

    # Numérotation
    numbering_prefix: Mapped[Optional[str]] = mapped_column(String(20))
    numbering_pattern: Mapped[Optional[str]] = mapped_column(String(50))  # FA-{YYYY}-{SEQ:6}
    numbering_reset: Mapped[Optional[str]] = mapped_column(String(20), default="yearly")  # yearly, monthly, never

    language: Mapped[Optional[str]] = mapped_column(String(5), default="fr")
    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    country_pack = relationship("CountryPack", back_populates="document_templates")

    __table_args__ = (
        Index("idx_doc_template_tenant_type", "tenant_id", "document_type"),
        Index("idx_doc_template_country", "country_pack_id"),
    )


class BankConfig(Base):
    """Configuration bancaire par pays."""
    __tablename__ = "country_bank_configs"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    country_pack_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    bank_format: Mapped[Optional[str]] = mapped_column(Enum(BankFormat), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Format IBAN/BIC
    iban_prefix: Mapped[Optional[str]] = mapped_column(String(2))  # FR, MA, etc.
    iban_length: Mapped[Optional[int]] = mapped_column(Integer)
    bic_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Format fichier
    export_format: Mapped[Optional[str]] = mapped_column(String(20))  # xml, csv, txt
    export_encoding: Mapped[Optional[str]] = mapped_column(String(20), default="utf-8")
    export_template: Mapped[Optional[str]] = mapped_column(Text)  # Template de fichier

    # Spécificités
    config: Mapped[Optional[dict]] = mapped_column(JSON)  # Config additionnelle

    is_default: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    country_pack = relationship("CountryPack", back_populates="bank_configs")

    __table_args__ = (
        Index("idx_bank_config_tenant", "tenant_id", "bank_format"),
        Index("idx_bank_config_country", "country_pack_id"),
    )


class PublicHoliday(Base):
    """Jours fériés par pays."""
    __tablename__ = "country_public_holidays"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    country_pack_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    name_local: Mapped[Optional[str]] = mapped_column(String(200))

    # Date
    holiday_date: Mapped[Optional[date]] = mapped_column(Date)  # Date fixe
    month: Mapped[Optional[int]] = mapped_column(Integer)      # 1-12 si récurrent
    day: Mapped[Optional[int]] = mapped_column(Integer)        # 1-31 si récurrent
    is_fixed: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)  # True=fixe, False=mobile (Pâques, etc.)
    calculation_rule: Mapped[Optional[str]] = mapped_column(String(100))  # Règle pour jours mobiles

    # Applicabilité
    year: Mapped[Optional[int]] = mapped_column(Integer)  # Si spécifique à une année
    region: Mapped[Optional[str]] = mapped_column(String(100))  # Si régional
    is_national: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Impact
    is_work_day: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    affects_banks: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    affects_business: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    country_pack = relationship("CountryPack", back_populates="holidays")

    __table_args__ = (
        Index("idx_holiday_tenant_date", "tenant_id", "holiday_date"),
        Index("idx_holiday_country", "country_pack_id"),
    )


class LegalRequirement(Base):
    """Exigences légales par pays."""
    __tablename__ = "country_legal_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    country_pack_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # fiscal, social, commercial
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Obligation
    requirement_type: Mapped[Optional[str]] = mapped_column(String(50))  # declaration, payment, report
    frequency: Mapped[Optional[str]] = mapped_column(String(20))  # monthly, quarterly, yearly
    deadline_rule: Mapped[Optional[str]] = mapped_column(String(100))  # Règle de calcul échéance

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON)

    # Références légales
    legal_reference: Mapped[Optional[str]] = mapped_column(String(200))
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    is_mandatory: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_legal_req_tenant_cat", "tenant_id", "category"),
        Index("idx_legal_req_country", "country_pack_id"),
    )


class TenantCountrySettings(Base):
    """Paramètres pays activés pour un tenant."""
    __tablename__ = "tenant_country_settings"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, index=True)

    country_pack_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("country_packs.id", ondelete="CASCADE"), nullable=False)

    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)  # Pays principal
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Overrides locaux
    custom_currency: Mapped[Optional[str]] = mapped_column(String(3))
    custom_language: Mapped[Optional[str]] = mapped_column(String(5))
    custom_timezone: Mapped[Optional[str]] = mapped_column(String(50))
    custom_config: Mapped[Optional[dict]] = mapped_column(JSON)

    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    activated_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    __table_args__ = (
        Index("idx_tenant_country_tenant", "tenant_id"),
        Index("idx_tenant_country_pack", "country_pack_id"),
    )
