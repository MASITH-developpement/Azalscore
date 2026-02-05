"""
AZALS MODULE - Contacts Unifiés - Modèles
=========================================

Modèles SQLAlchemy pour la gestion unifiée des contacts.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.types import UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class EntityType(str, enum.Enum):
    """Type d'entité (Particulier ou Société)."""
    INDIVIDUAL = "INDIVIDUAL"  # Particulier
    COMPANY = "COMPANY"        # Société


class RelationType(str, enum.Enum):
    """Type de relation commerciale."""
    CUSTOMER = "CUSTOMER"      # Client
    SUPPLIER = "SUPPLIER"      # Fournisseur


class AddressType(str, enum.Enum):
    """Type d'adresse."""
    BILLING = "BILLING"        # Facturation
    SHIPPING = "SHIPPING"      # Livraison
    SITE = "SITE"              # Chantier / Site
    HEAD_OFFICE = "HEAD_OFFICE"  # Siège social
    OTHER = "OTHER"            # Autre


class ContactPersonRole(str, enum.Enum):
    """Rôle d'une personne de contact."""
    MANAGER = "MANAGER"              # Dirigeant / Responsable
    COMMERCIAL = "COMMERCIAL"        # Commercial
    ACCOUNTING = "ACCOUNTING"        # Comptabilité
    BUYER = "BUYER"                  # Acheteur
    TECHNICAL = "TECHNICAL"          # Technique
    ADMINISTRATIVE = "ADMINISTRATIVE"  # Administratif
    LOGISTICS = "LOGISTICS"          # Logistique
    OTHER = "OTHER"                  # Autre


class CustomerType(str, enum.Enum):
    """Type de client (pour CRM)."""
    PROSPECT = "PROSPECT"
    LEAD = "LEAD"
    CUSTOMER = "CUSTOMER"
    VIP = "VIP"
    PARTNER = "PARTNER"
    CHURNED = "CHURNED"


class SupplierStatus(str, enum.Enum):
    """Statut fournisseur."""
    PROSPECT = "PROSPECT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    INACTIVE = "INACTIVE"


class SupplierType(str, enum.Enum):
    """Type de fournisseur."""
    GOODS = "GOODS"
    SERVICES = "SERVICES"
    BOTH = "BOTH"
    RAW_MATERIALS = "RAW_MATERIALS"
    EQUIPMENT = "EQUIPMENT"


# ============================================================================
# SEQUENCE NUMEROTATION
# ============================================================================

class ContactSequence(Base):
    """
    Séquence de numérotation par tenant et année.
    Utilisée pour générer CONT-YYYY-XXXX de manière transactionnelle.
    """
    __tablename__ = "contact_sequences"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    last_number = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'year', name='uq_contact_seq_tenant_year'),
        Index('idx_contact_seq_tenant_year', 'tenant_id', 'year'),
    )


# ============================================================================
# CONTACT UNIFIE
# ============================================================================

class UnifiedContact(Base):
    """
    Contact unifié (Client et/ou Fournisseur).

    Remplace les anciennes tables customers et purchases_suppliers.
    Permet de gérer une même entité comme client ET fournisseur.
    """
    __tablename__ = "contacts"

    # Identifiant
    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Code auto-généré (CONT-YYYY-XXXX)
    code = Column(String(20), nullable=False)

    # Type d'entité (Particulier / Société) - exclusif
    entity_type = Column(
        Enum(EntityType, name='contact_entity_type'),
        nullable=False,
        default=EntityType.COMPANY
    )

    # Types de relation (Client / Fournisseur) - multiple
    relation_types = Column(JSONB, nullable=False, default=list)

    # ========== IDENTIFICATION ==========
    # Nom principal (raison sociale ou nom complet)
    name = Column(String(255), nullable=False, index=True)
    # Raison sociale officielle (si société)
    legal_name = Column(String(255))
    # Prénom (si particulier)
    first_name = Column(String(100))
    # Nom de famille (si particulier)
    last_name = Column(String(100))

    # ========== COORDONNEES PRINCIPALES ==========
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))
    website = Column(String(255))

    # ========== INFORMATIONS LEGALES (Société) ==========
    tax_id = Column(String(50))              # N° TVA intracommunautaire
    registration_number = Column(String(50))  # SIRET
    legal_form = Column(String(50))          # SAS, SARL, EURL, etc.

    # ========== LOGO / PHOTO ==========
    logo_url = Column(String(500))           # URL du logo ou photo

    # ========== CONDITIONS CLIENT ==========
    customer_type = Column(
        Enum(CustomerType, name='contact_customer_type'),
        default=CustomerType.PROSPECT
    )
    customer_payment_terms = Column(String(50))      # NET_30, NET_60, etc.
    customer_payment_method = Column(String(50))     # BANK_TRANSFER, CHECK, etc.
    customer_credit_limit = Column(Numeric(15, 2))
    customer_discount_rate = Column(Numeric(5, 2), default=Decimal("0.00"))
    customer_currency = Column(String(3), default="EUR")

    # CRM
    assigned_to = Column(UniversalUUID())    # Commercial assigné
    industry = Column(String(100))           # Secteur d'activité
    source = Column(String(100))             # Source d'acquisition
    segment = Column(String(50))             # Segment marketing
    lead_score = Column(Integer, default=0)
    health_score = Column(Integer, default=100)

    # Statistiques client
    customer_total_revenue = Column(Numeric(15, 2), default=Decimal("0.00"))
    customer_order_count = Column(Integer, default=0)
    customer_last_order_date = Column(DateTime)
    customer_first_order_date = Column(DateTime)

    # ========== CONDITIONS FOURNISSEUR ==========
    supplier_status = Column(
        Enum(SupplierStatus, name='contact_supplier_status'),
        default=SupplierStatus.PROSPECT
    )
    supplier_type = Column(
        Enum(SupplierType, name='contact_supplier_type'),
        default=SupplierType.BOTH
    )
    supplier_payment_terms = Column(String(100))
    supplier_currency = Column(String(3), default="EUR")
    supplier_credit_limit = Column(Numeric(15, 2))
    supplier_category = Column(String(100))

    # Statistiques fournisseur
    supplier_total_purchases = Column(Numeric(15, 2), default=Decimal("0.00"))
    supplier_order_count = Column(Integer, default=0)
    supplier_last_order_date = Column(DateTime)

    # ========== CLASSIFICATION ==========
    tags = Column(JSONB, default=list)       # Tags libres

    # ========== NOTES ==========
    notes = Column(Text)                     # Notes publiques
    internal_notes = Column(Text)            # Notes internes

    # ========== METADONNEES ==========
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime)            # Soft delete
    created_by = Column(UniversalUUID())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ========== RELATIONS ==========
    persons = relationship(
        "ContactPerson",
        back_populates="unified_contact",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    addresses = relationship(
        "ContactAddress",
        back_populates="unified_contact",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # ========== INDEX ==========
    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_contacts_tenant_code'),
        Index('idx_contacts_tenant_name', 'tenant_id', 'name'),
        Index('idx_contacts_tenant_email', 'tenant_id', 'email'),
        Index('idx_contacts_tenant_entity_type', 'tenant_id', 'entity_type'),
        Index('idx_contacts_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_contacts_relation_types', 'relation_types', postgresql_using='gin'),
        Index('idx_contacts_tags', 'tags', postgresql_using='gin'),
    )

    # ========== PROPERTIES ==========
    @property
    def is_customer(self) -> bool:
        """Vérifie si le contact est un client."""
        return RelationType.CUSTOMER.value in (self.relation_types or [])

    @property
    def is_supplier(self) -> bool:
        """Vérifie si le contact est un fournisseur."""
        return RelationType.SUPPLIER.value in (self.relation_types or [])

    @property
    def display_name(self) -> str:
        """Nom d'affichage."""
        if self.entity_type == EntityType.INDIVIDUAL and self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.name

    @property
    def primary_person(self):
        """Retourne le contact principal."""
        return self.persons.filter_by(is_primary=True).first()

    @property
    def billing_address(self):
        """Retourne l'adresse de facturation par défaut."""
        return self.addresses.filter_by(
            address_type=AddressType.BILLING,
            is_default=True
        ).first()

    @property
    def shipping_address(self):
        """Retourne l'adresse de livraison par défaut."""
        return self.addresses.filter_by(
            address_type=AddressType.SHIPPING,
            is_default=True
        ).first()


# ============================================================================
# PERSONNE DE CONTACT
# ============================================================================

class ContactPerson(Base):
    """
    Personne de contact (Commercial, Comptabilité, Acheteur, etc.).
    Un contact peut avoir plusieurs personnes de contact.
    """
    __tablename__ = "contact_persons"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contact_id = Column(
        UniversalUUID(),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Rôle
    role = Column(
        Enum(ContactPersonRole, name='contact_person_role'),
        default=ContactPersonRole.OTHER
    )
    custom_role = Column(String(100))  # Rôle personnalisé si OTHER

    # Identité
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    job_title = Column(String(100))    # Fonction

    # Coordonnées
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))

    # Statut
    is_primary = Column(Boolean, default=False)  # Contact principal
    is_active = Column(Boolean, default=True)

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    unified_contact = relationship("UnifiedContact", back_populates="persons")

    # Index
    __table_args__ = (
        Index('idx_contact_persons_tenant_contact', 'tenant_id', 'contact_id'),
        Index('idx_contact_persons_role', 'contact_id', 'role'),
    )

    @property
    def full_name(self) -> str:
        """Nom complet."""
        return f"{self.first_name} {self.last_name}"

    @property
    def display_role(self) -> str:
        """Rôle affiché."""
        if self.role == ContactPersonRole.OTHER and self.custom_role:
            return self.custom_role
        return self.role.value if self.role else ""


# ============================================================================
# ADRESSE DE CONTACT
# ============================================================================

class ContactAddress(Base):
    """
    Adresse d'un contact (Facturation, Livraison, Chantier, etc.).
    Un contact peut avoir plusieurs adresses.
    """
    __tablename__ = "contact_addresses"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    contact_id = Column(
        UniversalUUID(),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Type et libellé
    address_type = Column(
        Enum(AddressType, name='contact_address_type'),
        nullable=False,
        default=AddressType.BILLING
    )
    label = Column(String(100))  # Libellé personnalisé (ex: "Chantier Paris")

    # Adresse
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    postal_code = Column(String(20))
    state = Column(String(100))       # Région / Province
    country_code = Column(String(3), default="FR")

    # Coordonnées GPS (optionnel)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))

    # Contact sur site
    contact_name = Column(String(255))
    contact_phone = Column(String(50))

    # Statut
    is_default = Column(Boolean, default=False)  # Adresse par défaut pour ce type
    is_active = Column(Boolean, default=True)

    # Notes
    notes = Column(Text)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    unified_contact = relationship("UnifiedContact", back_populates="addresses")

    # Index
    __table_args__ = (
        Index('idx_contact_addresses_tenant_contact', 'tenant_id', 'contact_id'),
        Index('idx_contact_addresses_type', 'contact_id', 'address_type'),
        Index('idx_contact_addresses_default', 'contact_id', 'address_type', 'is_default'),
    )

    @property
    def full_address(self) -> str:
        """Adresse complète sur une ligne."""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.postal_code} {self.city}" if self.postal_code or self.city else None,
            self.country_code
        ]
        return ", ".join(filter(None, parts))

    @property
    def display_label(self) -> str:
        """Libellé affiché."""
        if self.label:
            return self.label
        return self.address_type.value if self.address_type else "Adresse"
