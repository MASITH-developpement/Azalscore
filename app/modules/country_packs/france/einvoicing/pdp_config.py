"""
AZALSCORE - E-Invoicing PDP Configuration
Gestion des configurations PDP (Plateforme de Dématérialisation Partenaire)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.modules.country_packs.france.einvoicing_models import (
    CompanySizeType,
    EInvoiceFormatDB,
    EInvoiceRecord,
    PDPProviderType,
    TenantPDPConfig,
)
from app.modules.country_packs.france.einvoicing_schemas import (
    PDPConfigCreate,
    PDPConfigUpdate,
    PDPProviderType as SchemaProviderType,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PDPConfigManager:
    """
    Gestionnaire des configurations PDP.

    Gère le CRUD des configurations PDP pour un tenant.
    """

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def list_configs(
        self,
        active_only: bool = True,
        provider: SchemaProviderType | None = None
    ) -> list[TenantPDPConfig]:
        """Liste les configurations PDP du tenant."""
        query = self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.filter(TenantPDPConfig.is_active == True)

        if provider:
            query = query.filter(
                TenantPDPConfig.provider == PDPProviderType(provider.value)
            )

        return query.order_by(TenantPDPConfig.is_default.desc()).all()

    def get_config(self, config_id: uuid.UUID) -> TenantPDPConfig | None:
        """Récupère une configuration PDP."""
        return self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.id == config_id,
            TenantPDPConfig.tenant_id == self.tenant_id
        ).first()

    def get_default_config(self) -> TenantPDPConfig | None:
        """Récupère la configuration PDP par défaut."""
        return self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.tenant_id == self.tenant_id,
            TenantPDPConfig.is_default == True,
            TenantPDPConfig.is_active == True
        ).first()

    def create_config(
        self,
        data: PDPConfigCreate,
        created_by: uuid.UUID | None = None
    ) -> TenantPDPConfig:
        """Crée une configuration PDP."""
        # Si c'est la config par défaut, désactiver les autres
        if data.is_default:
            self._clear_default()

        config = TenantPDPConfig(
            tenant_id=self.tenant_id,
            provider=data.provider.value,
            name=data.name,
            description=data.description,
            api_url=data.api_url,
            token_url=data.token_url,
            client_id=data.client_id,
            client_secret=data.client_secret,
            scope=data.scope,
            certificate_ref=data.certificate_ref,
            private_key_ref=data.private_key_ref,
            siret=data.siret,
            siren=data.siren,
            tva_number=data.tva_number,
            company_size=data.company_size.value,
            is_active=data.is_active,
            is_default=data.is_default,
            test_mode=data.test_mode,
            timeout_seconds=data.timeout_seconds,
            retry_count=data.retry_count,
            webhook_url=data.webhook_url,
            webhook_secret=data.webhook_secret,
            preferred_format=data.preferred_format.value,
            generate_pdf=data.generate_pdf,
            provider_options=data.provider_options,
            custom_endpoints=data.custom_endpoints,
            created_by=created_by
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        logger.info(f"PDP config created: {config.id} for tenant {self.tenant_id}")
        return config

    def update_config(
        self,
        config_id: uuid.UUID,
        data: PDPConfigUpdate
    ) -> TenantPDPConfig | None:
        """Met à jour une configuration PDP."""
        config = self.get_config(config_id)
        if not config:
            return None

        # Gestion du flag default
        if data.is_default is True and not config.is_default:
            self._clear_default()

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "provider" and value:
                value = PDPProviderType(value.value)
            elif field == "company_size" and value:
                value = CompanySizeType(value.value)
            elif field == "preferred_format" and value:
                value = EInvoiceFormatDB(value.value)
            setattr(config, field, value)

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)

        return config

    def delete_config(self, config_id: uuid.UUID) -> bool:
        """Supprime une configuration PDP (soft delete si factures liées)."""
        config = self.get_config(config_id)
        if not config:
            return False

        # Vérifier s'il y a des factures liées
        has_invoices = self.db.query(EInvoiceRecord).filter(
            EInvoiceRecord.pdp_config_id == config_id
        ).first() is not None

        if has_invoices:
            # Soft delete
            config.is_active = False
            config.is_default = False
        else:
            # Hard delete
            self.db.delete(config)

        self.db.commit()
        return True

    def _clear_default(self) -> None:
        """Retire le flag default de toutes les configs."""
        self.db.query(TenantPDPConfig).filter(
            TenantPDPConfig.tenant_id == self.tenant_id,
            TenantPDPConfig.is_default == True
        ).update({"is_default": False})
