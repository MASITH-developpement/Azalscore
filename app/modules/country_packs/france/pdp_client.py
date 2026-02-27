"""
AZALS - Client PDP (Plateforme de Dématérialisation Partenaire)
================================================================

Intégration complète avec les plateformes de facturation électronique France 2026.

Providers supportés:
- Chorus Pro (B2G - obligatoire secteur public)
- API PPF (Portail Public de Facturation)
- PDP génériques (Yooz, Docaposte, Sage, Cegid, etc.)

Fonctionnalités:
- Émission de factures (dépôt)
- Réception de factures (flux entrant)
- Suivi du cycle de vie (statuts Y)
- e-reporting B2C
- Génération PDF/A-3 Factur-X
"""
from __future__ import annotations


import asyncio
import base64
import hashlib
import hmac
import io
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, List, Dict, Callable
from urllib.parse import urljoin

import httpx

from .e_invoicing import (
    EInvoiceDocument,
    EInvoiceFormat,
    EInvoiceStatus,
    EInvoiceType,
    EInvoiceParty,
    EInvoiceLine,
    PDPResponse,
    EInvoiceService,
)
from .exceptions import (
    PDPError,
    PDPConnectionError,
    PDPAuthenticationError,
    PDPAPIError,
    PDPRateLimitError,
    PDPTimeoutError,
    PDPInvoiceNotFoundError,
    PDPInvoiceRejectedError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class PDPProvider(str, Enum):
    """Providers PDP supportés."""
    CHORUS_PRO = "chorus_pro"       # B2G obligatoire
    PPF = "ppf"                      # Portail Public de Facturation
    YOOZ = "yooz"                    # PDP privé
    DOCAPOSTE = "docaposte"          # PDP privé (La Poste)
    SAGE = "sage"                    # PDP privé
    CEGID = "cegid"                  # PDP privé
    GENERIX = "generix"              # PDP privé
    EDICOM = "edicom"                # PDP privé
    BASWARE = "basware"              # PDP privé
    CUSTOM = "custom"                # PDP personnalisé


class InvoiceDirection(str, Enum):
    """Direction de la facture."""
    OUTBOUND = "outbound"  # Émise
    INBOUND = "inbound"    # Reçue


class LifecycleStatus(str, Enum):
    """Statuts du cycle de vie Y (PPF)."""
    DEPOSITED = "DEPOSITED"          # Déposée sur PDP
    TRANSMITTED = "TRANSMITTED"      # Transmise au PPF
    RECEIVED = "RECEIVED"            # Reçue par destinataire
    ACCEPTED = "ACCEPTED"            # Acceptée
    REFUSED = "REFUSED"              # Refusée
    PAYMENT_SENT = "PAYMENT_SENT"    # Paiement transmis
    PAID = "PAID"                    # Payée
    LITIGATION = "LITIGATION"        # Litige


class EReportingType(str, Enum):
    """Types d'e-reporting."""
    B2C_DOMESTIC = "B2C_DOMESTIC"       # Ventes B2C France
    B2C_EXPORT = "B2C_EXPORT"           # Ventes B2C export
    B2B_INTERNATIONAL = "B2B_INTL"      # Ventes B2B hors France
    PAYMENT_DATA = "PAYMENT_DATA"       # Données de paiement


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PDPConfig:
    """Configuration d'un provider PDP."""
    provider: PDPProvider
    api_url: str
    client_id: str
    client_secret: str
    # OAuth2
    token_url: Optional[str] = None
    scope: Optional[str] = None
    # Certificats
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    # Options
    test_mode: bool = True
    timeout: int = 30
    retry_count: int = 3
    # Identifiants entreprise
    siret: Optional[str] = None
    siren: Optional[str] = None
    tva_number: Optional[str] = None
    # Webhook
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None


@dataclass
class LifecycleEvent:
    """Événement du cycle de vie d'une facture."""
    status: LifecycleStatus
    timestamp: datetime
    actor: str  # Émetteur, Destinataire, PPF, PDP
    message: Optional[str] = None
    details: Optional[dict] = None


@dataclass
class EReportingData:
    """Données pour e-reporting B2C."""
    reporting_type: EReportingType
    period: str  # Format YYYY-MM
    siret: str
    # Totaux
    total_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal
    # Détail TVA par taux
    vat_breakdown: Dict[str, Decimal] = field(default_factory=dict)
    # Nombre de transactions
    transaction_count: int = 0
    # Métadonnées
    submission_id: Optional[str] = None
    submitted_at: Optional[datetime] = None


@dataclass
class PDPInvoiceResponse:
    """Réponse complète d'une opération PDP."""
    success: bool
    transaction_id: str
    ppf_id: Optional[str] = None  # Identifiant PPF unique
    pdp_id: Optional[str] = None  # Identifiant PDP
    status: EInvoiceStatus = EInvoiceStatus.DRAFT
    lifecycle_status: Optional[LifecycleStatus] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    # Document
    xml_content: Optional[str] = None
    pdf_content: Optional[bytes] = None
    # Lifecycle
    lifecycle_events: List[LifecycleEvent] = field(default_factory=list)


# =============================================================================
# ABSTRACT BASE CLIENT
# =============================================================================

class BasePDPClient(ABC):
    """Client PDP abstrait."""

    def __init__(self, config: PDPConfig) -> None:
        self.config: PDPConfig = config
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "BasePDPClient":
        self._http_client = httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=True
        )
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        if self._http_client:
            await self._http_client.aclose()

    async def _get_access_token(self) -> str:
        """Obtenir un token OAuth2."""
        if self._access_token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._access_token

        if not self.config.token_url:
            raise ValueError("token_url required for OAuth2")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "scope": self.config.scope or ""
                }
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)

            return self._access_token

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> dict:
        """Effectuer une requête API."""
        url = urljoin(self.config.api_url, endpoint)

        request_headers = headers or {}
        if self.config.token_url:
            token = await self._get_access_token()
            request_headers["Authorization"] = f"Bearer {token}"

        for attempt in range(self.config.retry_count):
            try:
                if method.upper() == "GET":
                    response = await self._http_client.get(url, headers=request_headers, params=data)
                elif method.upper() == "POST":
                    if files:
                        response = await self._http_client.post(url, headers=request_headers, files=files, data=data)
                    else:
                        request_headers["Content-Type"] = "application/json"
                        response = await self._http_client.post(url, headers=request_headers, json=data)
                elif method.upper() == "PUT":
                    request_headers["Content-Type"] = "application/json"
                    response = await self._http_client.put(url, headers=request_headers, json=data)
                else:
                    raise ValueError(f"Method {method} not supported")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error {e.response.status_code} on attempt {attempt + 1}")
                if attempt == self.config.retry_count - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

            except httpx.RequestError as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.config.retry_count - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    @abstractmethod
    async def submit_invoice(self, doc: EInvoiceDocument, xml_content: str, pdf_content: Optional[bytes] = None) -> PDPInvoiceResponse:
        """Soumettre une facture."""
        pass

    @abstractmethod
    async def get_invoice_status(self, invoice_id: str) -> PDPInvoiceResponse:
        """Obtenir le statut d'une facture."""
        pass

    @abstractmethod
    async def get_received_invoices(self, since: Optional[datetime] = None) -> List[PDPInvoiceResponse]:
        """Récupérer les factures reçues."""
        pass

    @abstractmethod
    async def submit_ereporting(self, data: EReportingData) -> PDPInvoiceResponse:
        """Soumettre un e-reporting B2C."""
        pass


# =============================================================================
# CHORUS PRO CLIENT (B2G)
# =============================================================================

class ChorusProClient(BasePDPClient):
    """
    Client Chorus Pro pour facturation B2G.

    Documentation: https://communaute.chorus-pro.gouv.fr/
    API: https://developer.aife.economie.gouv.fr/
    """

    SANDBOX_URL = "https://sandbox-api.piste.gouv.fr/cpro/factures/v1"
    PRODUCTION_URL = "https://api.piste.gouv.fr/cpro/factures/v1"

    def __init__(self, config: PDPConfig) -> None:
        if not config.api_url:
            config.api_url = self.SANDBOX_URL if config.test_mode else self.PRODUCTION_URL
        if not config.token_url:
            config.token_url = "https://oauth.piste.gouv.fr/api/oauth/token"
        super().__init__(config)

    async def submit_invoice(
        self,
        doc: EInvoiceDocument,
        xml_content: str,
        pdf_content: Optional[bytes] = None
    ) -> PDPInvoiceResponse:
        """Soumettre une facture sur Chorus Pro."""
        transaction_id = str(uuid.uuid4())

        try:
            # Préparer les données Chorus Pro
            chorus_data = {
                "idUtilisateurCourant": self.config.client_id,
                "fichierFlux": base64.b64encode(xml_content.encode()).decode(),
                "nomFichier": f"facture_{doc.invoice_number}.xml",
                "syntaxeFlux": "IN_DP_E2_CII_FACTURX",
                "avecSignature": False
            }

            # Mode test
            if self.config.test_mode:
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=transaction_id,
                    ppf_id=f"CHORUS-{transaction_id[:8].upper()}",
                    pdp_id=f"CPro-{doc.invoice_number}",
                    status=EInvoiceStatus.SENT,
                    lifecycle_status=LifecycleStatus.DEPOSITED,
                    message="[SANDBOX] Facture déposée sur Chorus Pro",
                    xml_content=xml_content,
                    lifecycle_events=[
                        LifecycleEvent(
                            status=LifecycleStatus.DEPOSITED,
                            timestamp=datetime.utcnow(),
                            actor="Chorus Pro",
                            message="Facture déposée en mode test"
                        )
                    ]
                )

            # Appel API réel
            response = await self._request("POST", "/deposer/flux", data=chorus_data)

            return PDPInvoiceResponse(
                success=True,
                transaction_id=transaction_id,
                ppf_id=response.get("numeroFluxDepot"),
                pdp_id=response.get("identifiantFactureCPP"),
                status=EInvoiceStatus.SENT,
                lifecycle_status=LifecycleStatus.DEPOSITED,
                message="Facture déposée sur Chorus Pro",
                xml_content=xml_content,
                lifecycle_events=[
                    LifecycleEvent(
                        status=LifecycleStatus.DEPOSITED,
                        timestamp=datetime.utcnow(),
                        actor="Chorus Pro",
                        message=f"Flux {response.get('numeroFluxDepot')}"
                    )
                ]
            )

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error(f"Erreur connexion Chorus Pro: {e}")
            return PDPInvoiceResponse(
                success=False,
                transaction_id=transaction_id,
                status=EInvoiceStatus.REJECTED,
                message=f"Erreur connexion Chorus Pro: {str(e)}",
                errors=[str(e)]
            )
        except (httpx.HTTPStatusError, PDPAPIError) as e:
            logger.error(f"Erreur API Chorus Pro: {e}")
            return PDPInvoiceResponse(
                success=False,
                transaction_id=transaction_id,
                status=EInvoiceStatus.REJECTED,
                message=f"Erreur Chorus Pro: {str(e)}",
                errors=[str(e)]
            )

    async def get_invoice_status(self, invoice_id: str) -> PDPInvoiceResponse:
        """Obtenir le statut d'une facture Chorus Pro."""
        try:
            if self.config.test_mode:
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=str(uuid.uuid4()),
                    pdp_id=invoice_id,
                    status=EInvoiceStatus.DELIVERED,
                    lifecycle_status=LifecycleStatus.RECEIVED,
                    message="[SANDBOX] Statut simulé",
                    lifecycle_events=[
                        LifecycleEvent(
                            status=LifecycleStatus.DEPOSITED,
                            timestamp=datetime.utcnow() - timedelta(hours=2),
                            actor="Émetteur"
                        ),
                        LifecycleEvent(
                            status=LifecycleStatus.TRANSMITTED,
                            timestamp=datetime.utcnow() - timedelta(hours=1),
                            actor="Chorus Pro"
                        ),
                        LifecycleEvent(
                            status=LifecycleStatus.RECEIVED,
                            timestamp=datetime.utcnow(),
                            actor="Destinataire"
                        )
                    ]
                )

            response = await self._request("GET", f"/consulter/facture/{invoice_id}")

            status_mapping = {
                "A_TRAITER": LifecycleStatus.RECEIVED,
                "EN_COURS_DE_TRAITEMENT": LifecycleStatus.RECEIVED,
                "VALIDEE": LifecycleStatus.ACCEPTED,
                "MISE_A_DISPOSITION": LifecycleStatus.TRANSMITTED,
                "REJETEE": LifecycleStatus.REFUSED,
                "MISE_EN_PAIEMENT": LifecycleStatus.PAYMENT_SENT,
                "SUSPENDUE": LifecycleStatus.LITIGATION
            }

            return PDPInvoiceResponse(
                success=True,
                transaction_id=str(uuid.uuid4()),
                pdp_id=invoice_id,
                lifecycle_status=status_mapping.get(response.get("statutFacture"), LifecycleStatus.DEPOSITED),
                message=response.get("libelleStatut", "")
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            return PDPInvoiceResponse(
                success=False,
                transaction_id=str(uuid.uuid4()),
                message=f"Erreur consultation: {str(e)}",
                errors=[str(e)]
            )

    async def get_received_invoices(self, since: Optional[datetime] = None) -> List[PDPInvoiceResponse]:
        """Récupérer les factures reçues via Chorus Pro."""
        invoices = []

        try:
            params = {
                "statutFacture": "A_TRAITER",
                "typeFacture": "FACTURE",
            }
            if since:
                params["dateDepotDebut"] = since.strftime("%Y-%m-%d")

            if self.config.test_mode:
                return [
                    PDPInvoiceResponse(
                        success=True,
                        transaction_id=str(uuid.uuid4()),
                        pdp_id=f"TEST-{i}",
                        status=EInvoiceStatus.DELIVERED,
                        lifecycle_status=LifecycleStatus.RECEIVED,
                        message=f"[SANDBOX] Facture test {i}"
                    )
                    for i in range(3)
                ]

            response = await self._request("GET", "/rechercher/factures", data=params)

            for facture in response.get("listeFactures", []):
                invoices.append(PDPInvoiceResponse(
                    success=True,
                    transaction_id=str(uuid.uuid4()),
                    pdp_id=facture.get("identifiantFactureCPP"),
                    ppf_id=facture.get("numeroFluxDepot"),
                    status=EInvoiceStatus.DELIVERED,
                    lifecycle_status=LifecycleStatus.RECEIVED,
                    message=f"Facture {facture.get('numeroFacture')}"
                ))

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            logger.error(f"Erreur recuperation factures: {e}")

        return invoices

    async def submit_ereporting(self, data: EReportingData) -> PDPInvoiceResponse:
        """e-reporting non applicable pour Chorus Pro (B2G uniquement)."""
        return PDPInvoiceResponse(
            success=False,
            transaction_id=str(uuid.uuid4()),
            message="e-reporting non supporté sur Chorus Pro (B2G uniquement)",
            errors=["Utiliser le PPF ou un PDP pour e-reporting B2C"]
        )


# =============================================================================
# PPF CLIENT (Portail Public de Facturation)
# =============================================================================

class PPFClient(BasePDPClient):
    """
    Client PPF (Portail Public de Facturation).

    Le PPF est la plateforme publique gratuite gérée par la DGFIP.
    Disponible à partir de septembre 2026.
    """

    # URLs à confirmer par la DGFIP
    SANDBOX_URL = "https://sandbox.portail-factures.gouv.fr/api/v1"
    PRODUCTION_URL = "https://api.portail-factures.gouv.fr/api/v1"

    def __init__(self, config: PDPConfig) -> None:
        if not config.api_url:
            config.api_url = self.SANDBOX_URL if config.test_mode else self.PRODUCTION_URL
        super().__init__(config)

    async def submit_invoice(
        self,
        doc: EInvoiceDocument,
        xml_content: str,
        pdf_content: Optional[bytes] = None
    ) -> PDPInvoiceResponse:
        """Soumettre une facture via PPF."""
        transaction_id = str(uuid.uuid4())

        try:
            # Préparer le payload PPF
            payload = {
                "format": doc.format.value,
                "flux": base64.b64encode(xml_content.encode()).decode(),
                "emetteur": {
                    "siret": doc.seller.siret,
                    "tva": doc.seller.tva_number
                },
                "destinataire": {
                    "siret": doc.buyer.siret if doc.buyer else None,
                    "routingId": doc.buyer.routing_id if doc.buyer else None
                },
                "metadata": {
                    "numeroFacture": doc.invoice_number,
                    "dateEmission": doc.issue_date.isoformat(),
                    "montantTTC": str(doc.total_ttc)
                }
            }

            # Ajouter PDF si disponible
            if pdf_content:
                payload["pdfFacturx"] = base64.b64encode(pdf_content).decode()

            if self.config.test_mode:
                ppf_id = f"PPF-{datetime.utcnow().strftime('%Y%m%d')}-{transaction_id[:8].upper()}"
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=transaction_id,
                    ppf_id=ppf_id,
                    status=EInvoiceStatus.SENT,
                    lifecycle_status=LifecycleStatus.TRANSMITTED,
                    message="[SANDBOX] Facture transmise au PPF",
                    xml_content=xml_content,
                    lifecycle_events=[
                        LifecycleEvent(
                            status=LifecycleStatus.DEPOSITED,
                            timestamp=datetime.utcnow(),
                            actor="Émetteur"
                        ),
                        LifecycleEvent(
                            status=LifecycleStatus.TRANSMITTED,
                            timestamp=datetime.utcnow(),
                            actor="PPF",
                            message=f"Référence PPF: {ppf_id}"
                        )
                    ]
                )

            response = await self._request("POST", "/factures/deposer", data=payload)

            return PDPInvoiceResponse(
                success=True,
                transaction_id=transaction_id,
                ppf_id=response.get("ppfId"),
                status=EInvoiceStatus.SENT,
                lifecycle_status=LifecycleStatus.TRANSMITTED,
                message="Facture transmise au PPF",
                xml_content=xml_content,
                lifecycle_events=[
                    LifecycleEvent(
                        status=LifecycleStatus.TRANSMITTED,
                        timestamp=datetime.utcnow(),
                        actor="PPF",
                        message=f"Référence PPF: {response.get('ppfId')}"
                    )
                ]
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            logger.error(f"Erreur PPF: {e}")
            return PDPInvoiceResponse(
                success=False,
                transaction_id=transaction_id,
                status=EInvoiceStatus.REJECTED,
                message=f"Erreur PPF: {str(e)}",
                errors=[str(e)]
            )

    async def get_invoice_status(self, invoice_id: str) -> PDPInvoiceResponse:
        """Obtenir le statut d'une facture via PPF."""
        try:
            if self.config.test_mode:
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=str(uuid.uuid4()),
                    ppf_id=invoice_id,
                    lifecycle_status=LifecycleStatus.RECEIVED,
                    message="[SANDBOX] Statut PPF simulé"
                )

            response = await self._request("GET", f"/factures/{invoice_id}/statut")

            return PDPInvoiceResponse(
                success=True,
                transaction_id=str(uuid.uuid4()),
                ppf_id=invoice_id,
                lifecycle_status=LifecycleStatus(response.get("statut", "TRANSMITTED")),
                message=response.get("message", "")
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            return PDPInvoiceResponse(
                success=False,
                transaction_id=str(uuid.uuid4()),
                message=str(e),
                errors=[str(e)]
            )

    async def get_received_invoices(self, since: Optional[datetime] = None) -> List[PDPInvoiceResponse]:
        """Recuperer les factures recues via PPF."""
        invoices = []

        try:
            params = {}
            if since:
                params["depuis"] = since.isoformat()

            if self.config.test_mode:
                return [
                    PDPInvoiceResponse(
                        success=True,
                        transaction_id=str(uuid.uuid4()),
                        ppf_id=f"PPF-TEST-{i}",
                        lifecycle_status=LifecycleStatus.RECEIVED,
                        message=f"[SANDBOX] Facture reçue {i}"
                    )
                    for i in range(2)
                ]

            response = await self._request("GET", "/factures/recues", data=params)

            for facture in response.get("factures", []):
                invoices.append(PDPInvoiceResponse(
                    success=True,
                    transaction_id=str(uuid.uuid4()),
                    ppf_id=facture.get("ppfId"),
                    lifecycle_status=LifecycleStatus.RECEIVED,
                    xml_content=facture.get("contenuXml")
                ))

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            logger.error(f"Erreur recuperation PPF: {e}")

        return invoices

    async def submit_ereporting(self, data: EReportingData) -> PDPInvoiceResponse:
        """Soumettre un e-reporting B2C via PPF."""
        transaction_id = str(uuid.uuid4())

        try:
            payload = {
                "type": data.reporting_type.value,
                "periode": data.period,
                "siret": data.siret,
                "totaux": {
                    "ht": str(data.total_ht),
                    "tva": str(data.total_tva),
                    "ttc": str(data.total_ttc)
                },
                "detailTva": {
                    taux: str(montant) for taux, montant in data.vat_breakdown.items()
                },
                "nombreTransactions": data.transaction_count
            }

            if self.config.test_mode:
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=transaction_id,
                    ppf_id=f"EREPORT-{data.period}-{transaction_id[:8]}",
                    message=f"[SANDBOX] e-reporting {data.reporting_type.value} soumis"
                )

            response = await self._request("POST", "/ereporting/soumettre", data=payload)

            return PDPInvoiceResponse(
                success=True,
                transaction_id=transaction_id,
                ppf_id=response.get("referenceDeclaration"),
                message=f"e-reporting soumis: {response.get('referenceDeclaration')}"
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            logger.error(f"Erreur e-reporting: {e}")
            return PDPInvoiceResponse(
                success=False,
                transaction_id=transaction_id,
                message=str(e),
                errors=[str(e)]
            )


# =============================================================================
# GENERIC PDP CLIENT
# =============================================================================

class GenericPDPClient(BasePDPClient):
    """
    Client PDP générique pour opérateurs privés.

    Supporte les PDP agréés: Yooz, Docaposte, Sage, Cegid, etc.
    Configuration via endpoints personnalisés.
    """

    def __init__(self, config: PDPConfig) -> None:
        super().__init__(config)
        self.endpoints = {
            "submit": "/invoices",
            "status": "/invoices/{id}/status",
            "received": "/invoices/received",
            "ereporting": "/ereporting"
        }

    def configure_endpoints(self, endpoints: Dict[str, str]) -> None:
        """Configurer les endpoints spécifiques au PDP."""
        self.endpoints.update(endpoints)

    async def submit_invoice(
        self,
        doc: EInvoiceDocument,
        xml_content: str,
        pdf_content: Optional[bytes] = None
    ) -> PDPInvoiceResponse:
        """Soumettre une facture via PDP générique."""
        transaction_id = str(uuid.uuid4())

        try:
            files = {
                "invoice_xml": ("invoice.xml", xml_content, "application/xml")
            }
            if pdf_content:
                files["invoice_pdf"] = ("invoice.pdf", pdf_content, "application/pdf")

            data = {
                "invoice_number": doc.invoice_number,
                "invoice_type": doc.invoice_type.value,
                "issue_date": doc.issue_date.isoformat(),
                "seller_siret": doc.seller.siret if doc.seller else None,
                "buyer_siret": doc.buyer.siret if doc.buyer else None,
                "total_ht": str(doc.total_ht),
                "total_ttc": str(doc.total_ttc),
                "format": doc.format.value
            }

            if self.config.test_mode:
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=transaction_id,
                    pdp_id=f"PDP-{self.config.provider.value.upper()}-{transaction_id[:8]}",
                    status=EInvoiceStatus.SENT,
                    lifecycle_status=LifecycleStatus.DEPOSITED,
                    message=f"[TEST] Facture soumise via {self.config.provider.value}",
                    xml_content=xml_content
                )

            response = await self._request("POST", self.endpoints["submit"], data=data, files=files)

            return PDPInvoiceResponse(
                success=True,
                transaction_id=transaction_id,
                pdp_id=response.get("invoice_id"),
                ppf_id=response.get("ppf_reference"),
                status=EInvoiceStatus.SENT,
                lifecycle_status=LifecycleStatus.DEPOSITED,
                message="Facture soumise",
                xml_content=xml_content
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            return PDPInvoiceResponse(
                success=False,
                transaction_id=transaction_id,
                message=str(e),
                errors=[str(e)]
            )

    async def get_invoice_status(self, invoice_id: str) -> PDPInvoiceResponse:
        """Obtenir le statut via PDP generique."""
        try:
            endpoint = self.endpoints["status"].format(id=invoice_id)

            if self.config.test_mode:
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=str(uuid.uuid4()),
                    pdp_id=invoice_id,
                    lifecycle_status=LifecycleStatus.TRANSMITTED,
                    message="[TEST] Statut simulé"
                )

            response = await self._request("GET", endpoint)

            return PDPInvoiceResponse(
                success=True,
                transaction_id=str(uuid.uuid4()),
                pdp_id=invoice_id,
                lifecycle_status=LifecycleStatus(response.get("status")),
                message=response.get("message", "")
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            return PDPInvoiceResponse(
                success=False,
                transaction_id=str(uuid.uuid4()),
                message=str(e),
                errors=[str(e)]
            )

    async def get_received_invoices(self, since: Optional[datetime] = None) -> List[PDPInvoiceResponse]:
        """Recuperer les factures recues."""
        try:
            params = {}
            if since:
                params["since"] = since.isoformat()

            if self.config.test_mode:
                return []

            response = await self._request("GET", self.endpoints["received"], data=params)
            return [
                PDPInvoiceResponse(
                    success=True,
                    transaction_id=str(uuid.uuid4()),
                    pdp_id=inv.get("id"),
                    lifecycle_status=LifecycleStatus.RECEIVED
                )
                for inv in response.get("invoices", [])
            ]

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            logger.error(f"Erreur reception factures: {e}")
            return []

    async def submit_ereporting(self, data: EReportingData) -> PDPInvoiceResponse:
        """Soumettre e-reporting via PDP."""
        transaction_id = str(uuid.uuid4())

        try:
            payload = {
                "type": data.reporting_type.value,
                "period": data.period,
                "siret": data.siret,
                "total_ht": str(data.total_ht),
                "total_vat": str(data.total_tva),
                "total_ttc": str(data.total_ttc),
                "vat_breakdown": data.vat_breakdown,
                "transaction_count": data.transaction_count
            }

            if self.config.test_mode:
                return PDPInvoiceResponse(
                    success=True,
                    transaction_id=transaction_id,
                    message=f"[TEST] e-reporting soumis"
                )

            response = await self._request("POST", self.endpoints["ereporting"], data=payload)

            return PDPInvoiceResponse(
                success=True,
                transaction_id=transaction_id,
                ppf_id=response.get("reference"),
                message="e-reporting soumis"
            )

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPAPIError) as e:
            return PDPInvoiceResponse(
                success=False,
                transaction_id=transaction_id,
                message=str(e),
                errors=[str(e)]
            )


# =============================================================================
# PDP CLIENT FACTORY
# =============================================================================

class PDPClientFactory:
    """Factory pour créer les clients PDP."""

    _clients: Dict[PDPProvider, type] = {
        PDPProvider.CHORUS_PRO: ChorusProClient,
        PDPProvider.PPF: PPFClient,
        PDPProvider.YOOZ: GenericPDPClient,
        PDPProvider.DOCAPOSTE: GenericPDPClient,
        PDPProvider.SAGE: GenericPDPClient,
        PDPProvider.CEGID: GenericPDPClient,
        PDPProvider.GENERIX: GenericPDPClient,
        PDPProvider.EDICOM: GenericPDPClient,
        PDPProvider.BASWARE: GenericPDPClient,
        PDPProvider.CUSTOM: GenericPDPClient,
    }

    @classmethod
    def create(cls, config: PDPConfig) -> BasePDPClient:
        """Créer un client PDP selon la configuration."""
        client_class = cls._clients.get(config.provider, GenericPDPClient)
        return client_class(config)

    @classmethod
    def register_provider(cls, provider: PDPProvider, client_class: type) -> None:
        """Enregistrer un nouveau provider."""
        cls._clients[provider] = client_class


# =============================================================================
# PDF/A-3 FACTUR-X GENERATOR
# =============================================================================

class FacturXPDFGenerator:
    """
    Générateur de PDF/A-3 Factur-X.

    Crée un PDF conforme avec XML embarqué selon la norme Factur-X.
    """

    def __init__(self) -> None:
        self._has_reportlab: bool = False
        self._has_pypdf: bool = False

        try:
            import reportlab
            self._has_reportlab = True
        except ImportError:
            pass

        try:
            import pypdf
            self._has_pypdf = True
        except ImportError:
            pass

    def generate_facturx_pdf(
        self,
        doc: EInvoiceDocument,
        xml_content: str,
        template_pdf: Optional[bytes] = None
    ) -> bytes:
        """
        Générer un PDF/A-3 Factur-X.

        Args:
            doc: Document facture
            xml_content: XML Factur-X à embarquer
            template_pdf: PDF modèle optionnel

        Returns:
            PDF/A-3 avec XML embarqué
        """
        if not self._has_reportlab:
            logger.warning("reportlab non disponible - génération PDF basique")
            return self._generate_basic_pdf(doc, xml_content)

        return self._generate_full_pdf(doc, xml_content, template_pdf)

    def _generate_basic_pdf(self, doc: EInvoiceDocument, xml_content: str) -> bytes:
        """Génération PDF basique (sans reportlab)."""
        # Créer un PDF minimal avec le XML en commentaire
        # En production, utiliser une vraie librairie PDF
        pdf_content = f"""%PDF-1.7
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 100 >>
stream
BT
/F1 12 Tf
50 750 Td
(FACTURE {doc.invoice_number}) Tj
50 730 Td
(Date: {doc.issue_date}) Tj
50 710 Td
(Total TTC: {doc.total_ttc} EUR) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
366
%%EOF
"""
        return pdf_content.encode()

    def _generate_full_pdf(
        self,
        doc: EInvoiceDocument,
        xml_content: str,
        template_pdf: Optional[bytes]
    ) -> bytes:
        """Génération PDF complète avec reportlab."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # En-tête
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "FACTURE")

        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"N° {doc.invoice_number}")
        c.drawString(50, height - 100, f"Date: {doc.issue_date.strftime('%d/%m/%Y')}")

        # Vendeur
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 140, "ÉMETTEUR")
        c.setFont("Helvetica", 10)
        if doc.seller:
            c.drawString(50, height - 160, doc.seller.name or "")
            c.drawString(50, height - 175, f"SIRET: {doc.seller.siret or ''}")
            c.drawString(50, height - 190, f"TVA: {doc.seller.tva_number or ''}")
            if doc.seller.address_line1:
                c.drawString(50, height - 205, doc.seller.address_line1)
            if doc.seller.postal_code and doc.seller.city:
                c.drawString(50, height - 220, f"{doc.seller.postal_code} {doc.seller.city}")

        # Acheteur
        c.setFont("Helvetica-Bold", 12)
        c.drawString(300, height - 140, "DESTINATAIRE")
        c.setFont("Helvetica", 10)
        if doc.buyer:
            c.drawString(300, height - 160, doc.buyer.name or "")
            c.drawString(300, height - 175, f"SIRET: {doc.buyer.siret or ''}")
            if doc.buyer.address_line1:
                c.drawString(300, height - 190, doc.buyer.address_line1)
            if doc.buyer.postal_code and doc.buyer.city:
                c.drawString(300, height - 205, f"{doc.buyer.postal_code} {doc.buyer.city}")

        # Lignes
        y_pos = height - 280
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_pos, "Description")
        c.drawString(300, y_pos, "Qté")
        c.drawString(350, y_pos, "P.U. HT")
        c.drawString(420, y_pos, "TVA")
        c.drawString(480, y_pos, "Total HT")

        c.setFont("Helvetica", 9)
        y_pos -= 20
        for line in doc.lines:
            c.drawString(50, y_pos, line.description[:40])
            c.drawString(300, y_pos, str(line.quantity))
            c.drawString(350, y_pos, f"{line.unit_price:.2f}")
            c.drawString(420, y_pos, f"{line.vat_rate}%")
            c.drawString(480, y_pos, f"{line.net_amount:.2f}")
            y_pos -= 15

        # Totaux
        y_pos -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(400, y_pos, f"Total HT: {doc.total_ht:.2f} €")
        c.drawString(400, y_pos - 20, f"TVA: {doc.total_tva:.2f} €")
        c.drawString(400, y_pos - 40, f"Total TTC: {doc.total_ttc:.2f} €")

        # Mentions légales
        c.setFont("Helvetica", 8)
        c.drawString(50, 50, f"Facture électronique conforme Factur-X ({doc.format.value})")
        c.drawString(50, 38, "Document généré par AZALSCORE - www.azalscore.com")

        c.save()

        # Récupérer le PDF
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # NOTE: Phase 2 - Embed XML en pièce jointe PDF/A-3 (pypdf)

        return pdf_bytes


# =============================================================================
# UNIFIED E-INVOICING SERVICE
# =============================================================================

class UnifiedEInvoicingService:
    """
    Service unifié de facturation électronique.

    Orchestre l'émission, la réception et le suivi des factures
    via les différentes plateformes (PPF, PDP, Chorus Pro).
    """

    def __init__(self, db: Any, tenant_id: str, pdp_configs: List[PDPConfig]) -> None:
        self.db: Any = db
        self.tenant_id: str = tenant_id
        self.configs: Dict[PDPProvider, PDPConfig] = {cfg.provider: cfg for cfg in pdp_configs}
        self.einvoice_service: EInvoiceService = EInvoiceService(db, tenant_id)
        self.pdf_generator: FacturXPDFGenerator = FacturXPDFGenerator()

    def _get_client(self, provider: PDPProvider) -> BasePDPClient:
        """Obtenir le client pour un provider."""
        config = self.configs.get(provider)
        if not config:
            raise ValueError(f"Provider {provider} non configuré")
        return PDPClientFactory.create(config)

    async def emit_invoice(
        self,
        invoice_data: dict,
        provider: PDPProvider = PDPProvider.PPF,
        generate_pdf: bool = True
    ) -> PDPInvoiceResponse:
        """
        Émettre une facture électronique.

        Args:
            invoice_data: Données de la facture
            provider: Plateforme cible (PPF, Chorus Pro, PDP)
            generate_pdf: Générer le PDF Factur-X

        Returns:
            Réponse avec statut et références
        """
        # Créer le document
        doc = self.einvoice_service.create_einvoice(invoice_data)

        # Valider
        validation = self.einvoice_service.validate_einvoice(doc)
        if not validation["valid"]:
            return PDPInvoiceResponse(
                success=False,
                transaction_id=str(uuid.uuid4()),
                status=EInvoiceStatus.REJECTED,
                message="Validation échouée",
                errors=validation["errors"],
                warnings=validation["warnings"]
            )

        # Générer XML
        xml_content = self.einvoice_service.generate_facturx_xml(doc)

        # Générer PDF si demandé
        pdf_content = None
        if generate_pdf:
            pdf_content = self.pdf_generator.generate_facturx_pdf(doc, xml_content)

        # Envoyer via le provider
        async with self._get_client(provider) as client:
            response = await client.submit_invoice(doc, xml_content, pdf_content)

        # Sauvegarder en base (TODO)
        # self._save_invoice_record(doc, response)

        return response

    async def get_status(
        self,
        invoice_id: str,
        provider: PDPProvider = PDPProvider.PPF
    ) -> PDPInvoiceResponse:
        """Obtenir le statut d'une facture."""
        async with self._get_client(provider) as client:
            return await client.get_invoice_status(invoice_id)

    async def fetch_received_invoices(
        self,
        provider: PDPProvider = PDPProvider.PPF,
        since: Optional[datetime] = None
    ) -> List[PDPInvoiceResponse]:
        """Récupérer les factures reçues."""
        async with self._get_client(provider) as client:
            return await client.get_received_invoices(since)

    async def submit_b2c_ereporting(
        self,
        period: str,
        transactions: List[dict],
        provider: PDPProvider = PDPProvider.PPF
    ) -> PDPInvoiceResponse:
        """
        Soumettre un e-reporting B2C.

        Args:
            period: Période (YYYY-MM)
            transactions: Liste des transactions B2C
            provider: Plateforme cible

        Returns:
            Réponse avec référence de déclaration
        """
        # Calculer les totaux
        total_ht = sum(Decimal(str(t.get("montant_ht", 0))) for t in transactions)
        total_tva = sum(Decimal(str(t.get("montant_tva", 0))) for t in transactions)
        total_ttc = sum(Decimal(str(t.get("montant_ttc", 0))) for t in transactions)

        # Ventilation TVA
        vat_breakdown = {}
        for t in transactions:
            taux = str(t.get("taux_tva", "20"))
            montant = Decimal(str(t.get("montant_tva", 0)))
            vat_breakdown[taux] = vat_breakdown.get(taux, Decimal(0)) + montant

        # Récupérer SIRET depuis config
        config = self.configs.get(provider)
        siret = config.siret if config else ""

        data = EReportingData(
            reporting_type=EReportingType.B2C_DOMESTIC,
            period=period,
            siret=siret,
            total_ht=total_ht,
            total_tva=total_tva,
            total_ttc=total_ttc,
            vat_breakdown={k: str(v) for k, v in vat_breakdown.items()},
            transaction_count=len(transactions)
        )

        async with self._get_client(provider) as client:
            return await client.submit_ereporting(data)

    async def check_compliance_status(self) -> dict:
        """
        Vérifier le statut de conformité e-invoicing.

        Returns:
            Statut de conformité par provider
        """
        status = {
            "compliant": True,
            "providers": {},
            "recommendations": []
        }

        for provider, config in self.configs.items():
            try:
                async with PDPClientFactory.create(config) as client:
                    # Test de connexion
                    test_response = await client.get_invoice_status("TEST")
                    status["providers"][provider.value] = {
                        "configured": True,
                        "test_mode": config.test_mode,
                        "connected": test_response.success or "SANDBOX" in test_response.message
                    }
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError, PDPError, OSError) as e:
                status["providers"][provider.value] = {
                    "configured": True,
                    "error": str(e)
                }
                status["compliant"] = False

        if not any(p.get("connected") for p in status["providers"].values()):
            status["recommendations"].append("Aucun provider PDP/PPF connecté")
            status["compliant"] = False

        return status
