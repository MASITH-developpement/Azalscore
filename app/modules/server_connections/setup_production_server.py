"""
AZALS - Script de configuration du serveur de production
=========================================================

Ce script configure le serveur de production 192.168.1.185 pour la gestion
du code Azalscore à distance.

Usage:
    python -m app.modules.server_connections.setup_production_server

Variables d'environnement:
    PROD_SERVER_HOST: Adresse IP du serveur (défaut: 192.168.1.185)
    PROD_SERVER_USER: Nom d'utilisateur SSH (défaut: azalscore)
    PROD_SERVER_PASSWORD: Mot de passe SSH (ou utiliser la clé SSH)
    PROD_SERVER_SSH_KEY: Chemin vers la clé SSH privée (optionnel)
"""

import os
import sys
import json
from pathlib import Path

# Configuration du serveur de production
DEFAULT_PRODUCTION_SERVER = {
    "name": "azals-production",
    "description": "Serveur de production Azalscore - 192.168.1.185",
    "host": os.getenv("PROD_SERVER_HOST", "192.168.1.185"),
    "port": int(os.getenv("PROD_SERVER_PORT", "22")),
    "username": os.getenv("PROD_SERVER_USER", "azalscore"),
    "connection_type": "SSH_PASSWORD",  # ou SSH_KEY si utilisation de clé
    "role": "PRODUCTION",
    "environment": "production",
    "working_directory": "/home/azalscore",
    "azalscore_path": "/opt/azalscore",
    "timeout_seconds": 30,
    "retry_count": 3,
    "is_default": True,
    "tags": ["production", "main", "france"],
}


def create_server_via_api():
    """
    Crée le serveur de production via l'API REST.

    Nécessite un token JWT valide et le X-Tenant-ID.
    """
    import httpx

    api_base = os.getenv("AZALS_API_URL", "http://localhost:8000")
    token = os.getenv("AZALS_API_TOKEN")
    tenant_id = os.getenv("AZALS_TENANT_ID", "masith")

    if not token:
        print("[ERROR] Variable AZALS_API_TOKEN requise")
        print("        Obtenez un token via: POST /v1/auth/login")
        return False

    # Ajouter le mot de passe ou la clé SSH
    server_data = DEFAULT_PRODUCTION_SERVER.copy()

    password = os.getenv("PROD_SERVER_PASSWORD")
    ssh_key_path = os.getenv("PROD_SERVER_SSH_KEY")

    if ssh_key_path and Path(ssh_key_path).exists():
        with open(ssh_key_path, "r") as f:
            server_data["private_key"] = f.read()
        server_data["connection_type"] = "SSH_KEY"
        passphrase = os.getenv("PROD_SERVER_SSH_PASSPHRASE")
        if passphrase:
            server_data["passphrase"] = passphrase
    elif password:
        server_data["password"] = password
    else:
        print("[ERROR] PROD_SERVER_PASSWORD ou PROD_SERVER_SSH_KEY requis")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
        "Content-Type": "application/json"
    }

    try:
        response = httpx.post(
            f"{api_base}/v1/servers",
            json=server_data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 201:
            server = response.json()
            print(f"[OK] Serveur créé avec succès: {server['name']} (ID: {server['id']})")
            return True
        elif response.status_code == 409:
            print("[INFO] Le serveur existe déjà")
            return True
        else:
            print(f"[ERROR] Erreur API: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"[ERROR] Erreur de connexion: {e}")
        return False


def test_ssh_connection():
    """
    Teste la connexion SSH directement sans passer par l'API.
    """
    from .clients.ssh import SSHClient, SSHConnectionError

    host = os.getenv("PROD_SERVER_HOST", "192.168.1.185")
    port = int(os.getenv("PROD_SERVER_PORT", "22"))
    username = os.getenv("PROD_SERVER_USER", "azalscore")
    password = os.getenv("PROD_SERVER_PASSWORD")
    ssh_key_path = os.getenv("PROD_SERVER_SSH_KEY")

    private_key = None
    if ssh_key_path and Path(ssh_key_path).exists():
        with open(ssh_key_path, "r") as f:
            private_key = f.read()

    if not password and not private_key:
        print("[ERROR] PROD_SERVER_PASSWORD ou PROD_SERVER_SSH_KEY requis")
        return False

    print(f"[...] Test de connexion SSH vers {username}@{host}:{port}")

    try:
        client = SSHClient(
            host=host,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
            timeout=10
        )

        result = client.test_connection()

        if result["success"]:
            print(f"[OK] Connexion SSH réussie (latence: {result['latency_ms']}ms)")
            print(f"     Serveur: {result.get('server_info', {}).get('server_version', 'N/A')}")

            # Tester une commande simple
            client.connect()
            info = client.get_system_info()
            print(f"     Hostname: {info.get('hostname', 'N/A')}")
            print(f"     OS: {info.get('os', 'N/A')}")
            print(f"     Kernel: {info.get('kernel', 'N/A')}")
            print(f"     CPU: {info.get('cpu_cores', 'N/A')} cores")

            client.disconnect()
            return True
        else:
            print(f"[ERROR] Connexion échouée: {result.get('error_message')}")
            return False

    except SSHConnectionError as e:
        print(f"[ERROR] Erreur SSH: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Erreur inattendue: {e}")
        return False


def print_configuration():
    """Affiche la configuration pour ajouter le serveur manuellement."""
    print("\n" + "=" * 60)
    print("CONFIGURATION SERVEUR DE PRODUCTION")
    print("=" * 60)
    print("\nPour ajouter le serveur via l'API REST, utilisez:")
    print("\nPOST /v1/servers")
    print("Headers:")
    print("  - Authorization: Bearer <votre_token>")
    print("  - X-Tenant-ID: <votre_tenant_id>")
    print("  - Content-Type: application/json")
    print("\nBody (JSON):")
    print(json.dumps(DEFAULT_PRODUCTION_SERVER, indent=2))
    print("\nN'oubliez pas d'ajouter 'password' ou 'private_key' au body.")
    print("=" * 60 + "\n")


def print_usage():
    """Affiche l'aide d'utilisation."""
    print("""
AZALS - Configuration du serveur de production
===============================================

Usage:
    python -m app.modules.server_connections.setup_production_server [commande]

Commandes:
    test    - Tester la connexion SSH au serveur
    create  - Créer le serveur via l'API REST
    config  - Afficher la configuration JSON
    help    - Afficher cette aide

Variables d'environnement:
    PROD_SERVER_HOST        - Adresse IP (défaut: 192.168.1.185)
    PROD_SERVER_PORT        - Port SSH (défaut: 22)
    PROD_SERVER_USER        - Utilisateur SSH (défaut: azalscore)
    PROD_SERVER_PASSWORD    - Mot de passe SSH
    PROD_SERVER_SSH_KEY     - Chemin vers la clé SSH privée
    PROD_SERVER_SSH_PASSPHRASE - Passphrase de la clé (si applicable)

    AZALS_API_URL           - URL de l'API (défaut: http://localhost:8000)
    AZALS_API_TOKEN         - Token JWT pour l'authentification
    AZALS_TENANT_ID         - ID du tenant (défaut: masith)

Exemples:
    # Test de connexion avec mot de passe
    PROD_SERVER_PASSWORD=secret python -m app.modules.server_connections.setup_production_server test

    # Test avec clé SSH
    PROD_SERVER_SSH_KEY=~/.ssh/id_rsa python -m app.modules.server_connections.setup_production_server test

    # Créer via l'API
    AZALS_API_TOKEN=xxx PROD_SERVER_PASSWORD=yyy python -m app.modules.server_connections.setup_production_server create
""")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command == "test":
        success = test_ssh_connection()
        sys.exit(0 if success else 1)
    elif command == "create":
        success = create_server_via_api()
        sys.exit(0 if success else 1)
    elif command == "config":
        print_configuration()
    else:
        print_usage()
