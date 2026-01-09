"""
AZALS MODULE - Server Connections
==================================

Module de gestion des connexions aux serveurs distants pour le déploiement
et la gestion du code Azalscore.

Fonctionnalités:
- Connexions SSH/SFTP sécurisées
- Gestion des identifiants chiffrés
- Exécution de commandes à distance
- Transfert de fichiers
- Surveillance de l'état des serveurs
- Déploiement et mise à jour du code
"""

# Configuration par défaut du premier serveur
DEFAULT_SERVER = {
    "name": "azals-production",
    "host": "192.168.1.185",
    "port": 22,
    "description": "Serveur de production Azalscore"
}

from .router import router
from .service import get_server_connection_service

__all__ = ["router", "get_server_connection_service", "DEFAULT_SERVER"]
