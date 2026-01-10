# AZALSCORE - Système d'Installation

Ce répertoire contient le système d'installation complet, automatisé et sécurisé pour déployer AZALSCORE sur n'importe quelle plateforme.

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Installation rapide](#installation-rapide)
- [Modes d'installation](#modes-dinstallation)
- [Plateformes supportées](#plateformes-supportées)
- [Variables d'environnement](#variables-denvironnement)
- [Sécurité](#sécurité)
- [Dépannage](#dépannage)
- [Structure des fichiers](#structure-des-fichiers)

## Vue d'ensemble

Le système d'installation AZALSCORE est conçu pour être :

- **Robuste** : Gestion des erreurs, vérifications préalables, rollback
- **Idempotent** : Peut être exécuté plusieurs fois sans effet indésirable
- **Sécurisé** : Génération dynamique des secrets, permissions strictes
- **Production-ready** : Configuration optimisée pour la production
- **Documenté** : Instructions claires pour chaque plateforme

## Installation rapide

### Linux / macOS

```bash
# Cloner le dépôt
git clone https://github.com/MASITH-developpement/Azalscore.git
cd Azalscore

# Rendre le script exécutable
chmod +x scripts/install/install.sh

# Lancer l'installation
./scripts/install/install.sh
```

### Windows (PowerShell 7+)

```powershell
# Cloner le dépôt
git clone https://github.com/MASITH-developpement/Azalscore.git
cd Azalscore

# Lancer l'installation (en administrateur)
.\scripts\install\install.ps1
```

### OVH VPS / Serveur dédié

```bash
# Installation en une commande
curl -fsSL https://raw.githubusercontent.com/MASITH-developpement/Azalscore/main/scripts/install/ovh/install_ovh.sh | sudo bash
```

## Modes d'installation

### Mode Développement (`--dev`)

Idéal pour le développement local :

- Debug activé
- Hot-reload activé
- Logs verbeux
- Documentation API accessible (/docs)
- CORS permissif (localhost autorisé)

```bash
./scripts/install/install.sh --dev
```

### Mode Production (`--prod`)

Pour les serveurs de production :

- Debug désactivé
- Service systemd configuré
- Pare-feu activé
- Logs de production (JSON)
- CORS strict
- Secrets forts générés

```bash
./scripts/install/install.sh --prod
```

### Mode Cloud (`--cloud`)

Préparation pour déploiement sur plateforme cloud :

- Génération du fichier .env avec secrets
- Instructions pour Railway/Render/Fly.io
- Pas d'installation système

```bash
./scripts/install/install.sh --cloud
```

## Plateformes supportées

### Systèmes d'exploitation

| OS | Version | Support |
|---|---|---|
| Debian | 11, 12 | ✅ Complet |
| Ubuntu | 20.04, 22.04, 24.04 | ✅ Complet |
| macOS | 12+ (Intel/ARM) | ✅ Complet |
| Windows | 10/11 (PowerShell 7+) | ✅ Complet |
| Fedora | 38+ | ✅ Complet |
| Arch Linux | Rolling | ✅ Complet |
| Alpine | 3.18+ | ⚠️ Docker uniquement |

### Plateformes cloud

| Plateforme | Documentation | Support |
|---|---|---|
| Railway | [railway.md](cloud/railway.md) | ✅ Complet |
| Render | [render.md](cloud/render.md) | ✅ Complet |
| Fly.io | [flyio.md](cloud/flyio.md) | ✅ Complet |
| Docker | [docker-compose.yml](cloud/docker-compose.yml) | ✅ Complet |
| OVH VPS | [install_ovh.sh](ovh/install_ovh.sh) | ✅ Complet |
| AWS EC2 | Via install.sh | ✅ Compatible |
| GCP | Via install.sh | ✅ Compatible |
| Azure | Via install.sh | ✅ Compatible |
| DigitalOcean | Via install.sh | ✅ Compatible |

## Variables d'environnement

### Variables obligatoires

| Variable | Description | Exemple |
|---|---|---|
| `DATABASE_URL` | URL de connexion PostgreSQL | `postgresql+psycopg2://user:pass@localhost:5432/azals` |
| `SECRET_KEY` | Clé secrète JWT (min 64 chars hex) | Généré automatiquement |
| `BOOTSTRAP_SECRET` | Secret pour création admin initial | Généré automatiquement |
| `ENVIRONMENT` | Environnement (dev/prod) | `production` |

### Variables de sécurité (production)

| Variable | Description | Obligatoire en prod |
|---|---|---|
| `ENCRYPTION_KEY` | Clé Fernet pour chiffrement AES-256 | ✅ Oui |
| `DEBUG` | Mode debug | ❌ Doit être `false` |
| `CORS_ORIGINS` | Domaines autorisés | ✅ Oui (pas de localhost) |
| `DB_STRICT_UUID` | Vérification stricte UUID | ✅ Doit être `true` |
| `DB_RESET_UUID` | Autoriser reset DB | ❌ Doit être `false` |

### Variables optionnelles

| Variable | Description | Défaut |
|---|---|---|
| `DB_POOL_SIZE` | Taille du pool de connexions | 5 (dev), 10 (prod) |
| `DB_MAX_OVERFLOW` | Connexions supplémentaires max | 10 (dev), 20 (prod) |
| `REDIS_URL` | URL Redis pour rate limiting | - |
| `RATE_LIMIT_PER_MINUTE` | Limite de requêtes/minute | 100 (dev), 60 (prod) |
| `AUTH_RATE_LIMIT_PER_MINUTE` | Limite auth/minute | 10 (dev), 5 (prod) |
| `LOG_LEVEL` | Niveau de log | DEBUG (dev), INFO (prod) |
| `API_WORKERS` | Nombre de workers | 1 (dev), auto (prod) |

## Sécurité

### Principes fondamentaux

1. **Aucun secret en dur** : Tous les secrets sont générés dynamiquement
2. **Secrets forts** : Minimum 32 bytes d'entropie cryptographique
3. **Permissions strictes** : Fichiers sensibles en mode 600
4. **UUID obligatoires** : Protection contre l'énumération
5. **Rate limiting** : Protection contre les abus
6. **CORS strict** : Pas de wildcard en production

### Génération des secrets

Les secrets sont générés avec des sources d'entropie cryptographiquement sûres :

```bash
# SECRET_KEY (256 bits)
openssl rand -hex 32

# BOOTSTRAP_SECRET (256 bits)
openssl rand -hex 32

# ENCRYPTION_KEY (Fernet AES-256)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Mot de passe PostgreSQL
openssl rand -base64 24
```

### Checklist de sécurité production

- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` généré (min 64 chars hex)
- [ ] `BOOTSTRAP_SECRET` unique
- [ ] `ENCRYPTION_KEY` est une clé Fernet valide
- [ ] `CORS_ORIGINS` ne contient PAS localhost
- [ ] `DB_STRICT_UUID=true`
- [ ] `DB_RESET_UUID=false`
- [ ] `DB_AUTO_RESET_ON_VIOLATION=false`
- [ ] Fichier `.env` en mode 600
- [ ] `.env` dans `.gitignore`
- [ ] HTTPS activé
- [ ] Pare-feu configuré
- [ ] Fail2ban actif
- [ ] Sauvegardes automatiques

## Dépannage

### L'installation échoue

```bash
# Vérifier les logs
cat install.log

# Vérifier les prérequis
./scripts/install/install.sh --help
```

### PostgreSQL ne démarre pas

```bash
# Vérifier le statut
sudo systemctl status postgresql

# Voir les logs
sudo journalctl -u postgresql -n 50
```

### L'application ne démarre pas

```bash
# Activer le venv et tester l'import
source venv/bin/activate
python -c "from app.main import app; print('OK')"

# Vérifier les migrations
alembic current
alembic upgrade head
```

### Erreur de connexion à la base de données

```bash
# Tester la connexion
psql $DATABASE_URL -c "SELECT 1;"

# Vérifier les permissions
sudo -u postgres psql -c "\du"
```

### Port déjà utilisé

```bash
# Trouver le processus
sudo lsof -i :8000
sudo lsof -i :5432

# Arrêter le processus
sudo kill -9 <PID>
```

## Structure des fichiers

```
scripts/install/
├── install.sh                 # Point d'entrée principal (Linux/macOS)
├── install.ps1                # Point d'entrée Windows
├── README.md                  # Cette documentation
│
├── common/                    # Modules partagés
│   ├── checks.sh              # Vérifications système
│   ├── env_generator.sh       # Génération .env
│   ├── secrets.sh             # Génération secrets
│   ├── postgres.sh            # Installation PostgreSQL
│   ├── python.sh              # Installation Python + venv
│   ├── azalscore.sh           # Installation application
│   ├── systemd.sh             # Service systemd
│   ├── firewall.sh            # Configuration pare-feu
│   └── summary.sh             # Rapport final
│
├── cloud/                     # Déploiement cloud
│   ├── railway.md             # Instructions Railway
│   ├── render.md              # Instructions Render
│   ├── flyio.md               # Instructions Fly.io
│   ├── docker-compose.yml     # Configuration Docker
│   ├── nginx.conf             # Configuration Nginx
│   ├── init-db.sh             # Initialisation PostgreSQL
│   └── backup.sh              # Script de sauvegarde
│
└── ovh/                       # Serveurs OVH
    ├── install_ovh.sh         # Installation complète OVH
    └── hardening.sh           # Sécurisation serveur
```

## Commandes post-installation

### Démarrer l'application

```bash
# Mode développement
./start_dev.sh

# Mode production
sudo systemctl start azalscore
```

### Gérer le service (production)

```bash
# Statut
sudo systemctl status azalscore

# Logs
sudo journalctl -u azalscore -f

# Redémarrer
sudo systemctl restart azalscore
```

### Migrations

```bash
# Activer le venv
source venv/bin/activate

# Voir l'état
alembic current

# Appliquer les migrations
alembic upgrade head

# Créer une migration
alembic revision --autogenerate -m "description"
```

### Sauvegardes

```bash
# Sauvegarde manuelle
pg_dump -U azals_user azals > backup_$(date +%Y%m%d).sql

# Restauration
psql -U azals_user azals < backup.sql
```

## Support

- **Documentation** : https://github.com/MASITH-developpement/Azalscore
- **Issues** : https://github.com/MASITH-developpement/Azalscore/issues
- **Logs d'installation** : `install.log` dans le répertoire du projet

## Licence

Ce projet est sous licence propriétaire. Voir le fichier LICENSE pour plus de détails.

---

*Système d'installation AZALSCORE v1.0.0*
