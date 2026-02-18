"""
AZALS MODULE - Odoo Import - Connector
=======================================

Client XML-RPC pour communiquer avec Odoo (versions 8-18).
Gere l'authentification, les requetes et les erreurs.

SÉCURITÉ: defusedxml monkey-patch appliqué pour protéger
contre les attaques XML (XXE, billion laughs, etc.)
"""

import logging
import ssl

# SÉCURITÉ: Monkey-patch xmlrpc.client AVANT import
# Protection contre XXE et autres attaques XML (bandit B411)
import defusedxml.xmlrpc
defusedxml.xmlrpc.monkey_patch()

import xmlrpc.client  # noqa: E402  # nosec B411 - monkey-patch appliqué ligne 15-16
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class OdooConnectionError(Exception):
    """Erreur de connexion a Odoo."""
    pass


class OdooAuthenticationError(Exception):
    """Erreur d'authentification Odoo."""
    pass


class OdooAPIError(Exception):
    """Erreur lors d'un appel API Odoo."""
    pass


class OdooConnector:
    """
    Client XML-RPC pour Odoo.

    Compatible avec Odoo versions 8 a 18.
    Supporte l'authentification par mot de passe et API key.

    Usage:
        connector = OdooConnector(
            url="https://mycompany.odoo.com",
            database="mydb",
            username="admin",
            credential="api_key_or_password",
            auth_method="api_key"  # ou "password"
        )
        await connector.connect()
        products = await connector.search_read("product.product", [], ["name", "default_code"])
    """

    def __init__(
        self,
        url: str,
        database: str,
        username: str,
        credential: str,
        auth_method: str = "api_key",
        timeout: int = 30,
    ):
        """
        Initialise le connecteur Odoo.

        Args:
            url: URL de l'instance Odoo (ex: https://mycompany.odoo.com)
            database: Nom de la base de donnees Odoo
            username: Nom d'utilisateur Odoo
            credential: Mot de passe ou API key
            auth_method: "password" ou "api_key"
            timeout: Timeout en secondes pour les requetes
        """
        self.url = url.rstrip('/')
        self.database = database
        self.username = username
        self.credential = credential
        self.auth_method = auth_method
        self.timeout = timeout

        self._uid: Optional[int] = None
        self._common: Optional[xmlrpc.client.ServerProxy] = None
        self._object: Optional[xmlrpc.client.ServerProxy] = None
        self._version: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """Verifie si la connexion est etablie."""
        return self._uid is not None

    @property
    def version(self) -> Optional[str]:
        """Retourne la version Odoo detectee."""
        return self._version

    def _create_proxy(self, endpoint: str) -> xmlrpc.client.ServerProxy:
        """Cree un proxy XML-RPC avec SSL configurable."""
        full_url = f"{self.url}/xmlrpc/2/{endpoint}"

        # Creer un contexte SSL qui accepte les certificats auto-signes (dev)
        context = ssl.create_default_context()
        # En production, on devrait verifier les certificats
        # context.check_hostname = False
        # context.verify_mode = ssl.CERT_NONE

        return xmlrpc.client.ServerProxy(
            full_url,
            context=context,
            allow_none=True,
        )

    def connect(self) -> Tuple[bool, str]:
        """
        Etablit la connexion a Odoo.

        Returns:
            Tuple (success, message)
        """
        try:
            # Creer les proxies
            self._common = self._create_proxy("common")
            self._object = self._create_proxy("object")

            # Recuperer la version
            try:
                version_info = self._common.version()
                if version_info and isinstance(version_info, dict):
                    self._version = version_info.get('server_version', 'unknown')
                    logger.info(f"[ODOO] Version detectee: {self._version}")
            except Exception as e:
                logger.warning(f"[ODOO] Impossible de recuperer la version: {e}")
                self._version = "unknown"

            # Authentification
            # Pour les API keys (Odoo 14+), on utilise la cle comme mot de passe
            password = self.credential

            try:
                self._uid = self._common.authenticate(
                    self.database,
                    self.username,
                    password,
                    {}
                )
            except xmlrpc.client.Fault as e:
                if "Access Denied" in str(e) or "authentication" in str(e).lower():
                    raise OdooAuthenticationError(
                        f"Authentification echouee: verifiez vos identifiants. "
                        f"Pour Odoo 14+, utilisez une API key au lieu du mot de passe."
                    )
                raise

            if not self._uid:
                raise OdooAuthenticationError(
                    "Authentification echouee: identifiants invalides"
                )

            logger.info(
                f"[ODOO] Connexion etablie - URL: {self.url}, "
                f"DB: {self.database}, UID: {self._uid}"
            )
            return True, f"Connexion etablie (Odoo {self._version})"

        except OdooAuthenticationError:
            raise
        except xmlrpc.client.ProtocolError as e:
            raise OdooConnectionError(
                f"Erreur de protocole: {e.errcode} {e.errmsg}. "
                f"Verifiez l'URL: {self.url}"
            )
        except ConnectionRefusedError:
            raise OdooConnectionError(
                f"Connexion refusee. Verifiez que Odoo est accessible: {self.url}"
            )
        except Exception as e:
            raise OdooConnectionError(f"Erreur de connexion: {str(e)}")

    def _ensure_connected(self):
        """Verifie que la connexion est etablie."""
        if not self.is_connected:
            raise OdooConnectionError("Non connecte. Appelez connect() d'abord.")

    def execute_kw(
        self,
        model: str,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute une methode sur un modele Odoo.

        Args:
            model: Nom du modele (ex: "product.product")
            method: Nom de la methode (ex: "search_read")
            args: Arguments positionnels
            kwargs: Arguments nommes

        Returns:
            Resultat de l'appel API
        """
        self._ensure_connected()

        if kwargs is None:
            kwargs = {}

        try:
            result = self._object.execute_kw(
                self.database,
                self._uid,
                self.credential,
                model,
                method,
                args,
                kwargs,
            )
            return result

        except xmlrpc.client.Fault as e:
            # Erreur Odoo (ex: modele inexistant, droits insuffisants)
            raise OdooAPIError(f"Erreur Odoo sur {model}.{method}: {e.faultString}")
        except Exception as e:
            raise OdooAPIError(f"Erreur API: {str(e)}")

    def search(
        self,
        model: str,
        domain: List[Any],
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> List[int]:
        """
        Recherche des IDs dans un modele Odoo.

        Args:
            model: Nom du modele
            domain: Domaine de recherche Odoo (ex: [("active", "=", True)])
            offset: Offset pour pagination
            limit: Limite de resultats
            order: Ordre de tri (ex: "name asc")

        Returns:
            Liste des IDs trouves
        """
        kwargs = {}
        if offset:
            kwargs['offset'] = offset
        if limit:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order

        return self.execute_kw(model, 'search', [domain], kwargs)

    def search_count(self, model: str, domain: List[Any]) -> int:
        """
        Compte les enregistrements correspondant au domaine.

        Args:
            model: Nom du modele
            domain: Domaine de recherche

        Returns:
            Nombre d'enregistrements
        """
        return self.execute_kw(model, 'search_count', [domain])

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lit les enregistrements par ID.

        Args:
            model: Nom du modele
            ids: Liste des IDs a lire
            fields: Liste des champs a retourner (tous si None)

        Returns:
            Liste des enregistrements
        """
        kwargs = {}
        if fields:
            kwargs['fields'] = fields

        return self.execute_kw(model, 'read', [ids], kwargs)

    def search_read(
        self,
        model: str,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recherche et lit en une seule requete.

        Args:
            model: Nom du modele
            domain: Domaine de recherche
            fields: Champs a retourner
            offset: Offset pagination
            limit: Limite resultats
            order: Ordre de tri

        Returns:
            Liste des enregistrements
        """
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        if offset:
            kwargs['offset'] = offset
        if limit:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order

        return self.execute_kw(model, 'search_read', [domain], kwargs)

    def fields_get(
        self,
        model: str,
        attributes: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Recupere les metadonnees des champs d'un modele.

        Args:
            model: Nom du modele
            attributes: Attributs a recuperer (ex: ['string', 'type', 'required'])

        Returns:
            Dictionnaire des champs avec leurs attributs
        """
        kwargs = {}
        if attributes:
            kwargs['attributes'] = attributes

        return self.execute_kw(model, 'fields_get', [], kwargs)

    def get_models(self) -> List[str]:
        """
        Liste les modeles disponibles dans Odoo.

        Returns:
            Liste des noms de modeles
        """
        models = self.search_read(
            'ir.model',
            [('transient', '=', False)],
            ['model', 'name'],
            limit=1000,
        )
        return [m['model'] for m in models]

    def get_modified_since(
        self,
        model: str,
        since: datetime,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recupere les enregistrements modifies depuis une date.
        Utilise pour le delta sync.

        Args:
            model: Nom du modele
            since: Date de derniere synchronisation
            fields: Champs a recuperer
            limit: Limite de resultats

        Returns:
            Liste des enregistrements modifies
        """
        # Format datetime pour Odoo
        since_str = since.strftime('%Y-%m-%d %H:%M:%S')

        domain = [
            '|',
            ('write_date', '>=', since_str),
            ('create_date', '>=', since_str),
        ]

        return self.search_read(
            model,
            domain,
            fields=fields,
            limit=limit,
            order='write_date asc',
        )

    def get_categories(self) -> List[Dict[str, Any]]:
        """Recupere les categories de produits."""
        return self.search_read(
            'product.category',
            [],
            ['id', 'name', 'parent_id', 'complete_name'],
        )

    def get_uom(self) -> List[Dict[str, Any]]:
        """Recupere les unites de mesure."""
        return self.search_read(
            'uom.uom',
            [],
            ['id', 'name', 'category_id', 'uom_type', 'factor'],
        )

    def get_countries(self) -> List[Dict[str, Any]]:
        """Recupere la liste des pays."""
        return self.search_read(
            'res.country',
            [],
            ['id', 'name', 'code'],
        )

    def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion et retourne des informations sur l'instance.

        Returns:
            Dictionnaire avec les informations de connexion
        """
        success, message = self.connect()

        if not success:
            return {
                'success': False,
                'message': message,
            }

        # Recuperer des infos supplementaires
        try:
            user_info = self.read('res.users', [self._uid], ['name', 'email', 'login'])
            user = user_info[0] if user_info else {}

            # Verifier les modeles disponibles
            available_models = []
            for model in ['product.product', 'res.partner', 'purchase.order']:
                try:
                    count = self.search_count(model, [])
                    available_models.append(f"{model} ({count} records)")
                except OdooAPIError:
                    pass

            return {
                'success': True,
                'message': message,
                'odoo_version': self._version,
                'database_name': self.database,
                'user_name': user.get('name', self.username),
                'user_email': user.get('email'),
                'available_models': available_models,
            }

        except Exception as e:
            return {
                'success': True,
                'message': f"{message} (infos partielles: {e})",
                'odoo_version': self._version,
                'database_name': self.database,
            }
