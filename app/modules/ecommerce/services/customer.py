"""
AZALS MODULE 12 - E-Commerce Customer Service
===============================================

Gestion des clients e-commerce.
"""
from __future__ import annotations


import logging
from datetime import datetime
from typing import List, Optional, Tuple

import bcrypt

from app.modules.ecommerce.models import CustomerAddress, EcommerceCustomer
from app.modules.ecommerce.schemas import CustomerAddressCreate, CustomerRegisterRequest

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class CustomerService(BaseEcommerceService[EcommerceCustomer]):
    """Service de gestion des clients."""

    model = EcommerceCustomer

    def register(
        self,
        data: CustomerRegisterRequest,
    ) -> Tuple[Optional[EcommerceCustomer], str]:
        """Inscrit un nouveau client."""
        # Vérifier si l'email existe
        existing = (
            self._base_query()
            .filter(EcommerceCustomer.email == data.email)
            .first()
        )

        if existing:
            return None, "Email déjà utilisé"

        # Hasher le mot de passe avec bcrypt
        password_hash = bcrypt.hashpw(
            data.password.encode(),
            bcrypt.gensalt(),
        ).decode()

        customer = EcommerceCustomer(
            tenant_id=self.tenant_id,
            email=data.email,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            accepts_marketing=data.accepts_marketing,
            marketing_opt_in_at=(
                datetime.utcnow() if data.accepts_marketing else None
            ),
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        logger.info(
            "Customer registered | tenant=%s customer_id=%s email=%s",
            self.tenant_id,
            customer.id,
            customer.email,
        )
        return customer, "Inscription réussie"

    def get(self, customer_id: int) -> Optional[EcommerceCustomer]:
        """Récupère un client par ID."""
        return self._get_by_id(customer_id)

    def get_by_email(self, email: str) -> Optional[EcommerceCustomer]:
        """Récupère un client par email."""
        return (
            self._base_query()
            .filter(EcommerceCustomer.email == email)
            .first()
        )

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> Optional[EcommerceCustomer]:
        """Authentifie un client."""
        customer = self.get_by_email(email)
        if not customer or not customer.password_hash:
            return None

        if not bcrypt.checkpw(
            password.encode(),
            customer.password_hash.encode(),
        ):
            return None

        # Mettre à jour la dernière connexion
        customer.last_login_at = datetime.utcnow()
        self.db.commit()

        return customer

    def update(
        self,
        customer_id: int,
        data: dict,
    ) -> Optional[EcommerceCustomer]:
        """Met à jour un client."""
        customer = self.get(customer_id)
        if not customer:
            return None

        # Hasher le nouveau mot de passe si fourni
        if "password" in data:
            data["password_hash"] = bcrypt.hashpw(
                data.pop("password").encode(),
                bcrypt.gensalt(),
            ).decode()

        return self._update(customer, data)

    def deactivate(self, customer_id: int) -> bool:
        """Désactive un client."""
        customer = self.get(customer_id)
        if not customer:
            return False

        customer.is_active = False
        self.db.commit()
        return True

    # =========================================================================
    # ADDRESSES
    # =========================================================================

    def add_address(
        self,
        customer_id: int,
        data: CustomerAddressCreate,
    ) -> CustomerAddress:
        """Ajoute une adresse au client."""
        address = CustomerAddress(
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            **data.model_dump(),
        )
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def get_addresses(self, customer_id: int) -> List[CustomerAddress]:
        """Liste les adresses d'un client."""
        return (
            self.db.query(CustomerAddress)
            .filter(
                CustomerAddress.tenant_id == self.tenant_id,
                CustomerAddress.customer_id == customer_id,
            )
            .all()
        )

    def get_address(
        self,
        customer_id: int,
        address_id: int,
    ) -> Optional[CustomerAddress]:
        """Récupère une adresse."""
        return (
            self.db.query(CustomerAddress)
            .filter(
                CustomerAddress.tenant_id == self.tenant_id,
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.id == address_id,
            )
            .first()
        )

    def update_address(
        self,
        customer_id: int,
        address_id: int,
        data: dict,
    ) -> Optional[CustomerAddress]:
        """Met à jour une adresse."""
        address = self.get_address(customer_id, address_id)
        if not address:
            return None

        for field, value in data.items():
            if hasattr(address, field):
                setattr(address, field, value)

        self.db.commit()
        self.db.refresh(address)
        return address

    def delete_address(
        self,
        customer_id: int,
        address_id: int,
    ) -> bool:
        """Supprime une adresse."""
        address = self.get_address(customer_id, address_id)
        if not address:
            return False

        self.db.delete(address)
        self.db.commit()
        return True

    def set_default_address(
        self,
        customer_id: int,
        address_id: int,
        address_type: str = "both",
    ) -> bool:
        """
        Définit une adresse comme adresse par défaut.

        Args:
            customer_id: ID du client
            address_id: ID de l'adresse
            address_type: "billing", "shipping" ou "both"

        Returns:
            True si mis à jour
        """
        address = self.get_address(customer_id, address_id)
        if not address:
            return False

        # Réinitialiser les autres adresses
        all_addresses = self.get_addresses(customer_id)
        for addr in all_addresses:
            if address_type in ("billing", "both"):
                addr.is_default_billing = addr.id == address_id
            if address_type in ("shipping", "both"):
                addr.is_default_shipping = addr.id == address_id

        self.db.commit()
        return True
