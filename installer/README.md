# AZALSCORE - Package d'Installation Universel

## Vue d'Ensemble

Ce package permet d'installer AZALSCORE sur n'importe quelle plateforme supportant Docker, sans dépendance cloud ni intervention humaine.

## Plateformes Supportées

| Plateforme | Architecture | Statut |
|------------|--------------|--------|
| Linux (Debian/Ubuntu) | amd64, arm64 | ✅ Complet |
| Linux (RHEL/CentOS/Fedora) | amd64, arm64 | ✅ Complet |
| Linux (Alpine) | amd64, arm64 | ✅ Complet |
| macOS | Intel (amd64) | ✅ Docker Desktop |
| macOS | Apple Silicon (arm64) | ✅ Docker Desktop |
| Windows | amd64 | ✅ Docker Desktop |

## Prérequis

- **Docker** 20.10+ et Docker Compose v2
- **RAM**: 2 GB minimum (4 GB recommandé)
- **Disque**: 10 GB minimum
- **Réseau**: Accès sortant pour télécharger les images

## Installation Rapide

```bash
# 1. Télécharger le package
curl -LO https://github.com/MASITH-developpement/Azalscore/releases/latest/download/azalscore-installer.tar.gz

# 2. Extraire
tar -xzf azalscore-installer.tar.gz
cd azalscore-installer

# 3. Installer
chmod +x install.sh
./install.sh
```

## Installation Automatique (Headless)

Pour les environnements CI/CD ou serveurs sans interface :

```bash
./install.sh --auto
```

## Options du Script

```
./install.sh [OPTIONS]

OPTIONS:
    --auto          Installation automatique (mode headless)
    --uninstall     Désinstallation complète
    --upgrade       Mise à jour vers la dernière version
    --backup        Créer une sauvegarde
    --restore DATE  Restaurer depuis une sauvegarde
    --test          Exécuter les tests de validation
    --status        Afficher le statut des services
    --logs          Afficher les logs
    --help          Afficher cette aide
```

## Configuration

### Variables d'Environnement

Le fichier `.env` est généré automatiquement avec des secrets sécurisés. Personnalisez selon vos besoins :

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `SECRET_KEY` | Clé JWT (min 64 chars) | ✅ |
| `ENCRYPTION_KEY` | Clé Fernet pour chiffrement | ✅ |
| `DATABASE_URL` | URL PostgreSQL | ✅ |
| `ADMIN_EMAIL` | Email admin initial | ✅ |
| `ADMIN_PASSWORD` | Mot de passe admin (min 12 chars) | ✅ |
| `CORS_ORIGINS` | Origines CORS autorisées | ✅ en prod |
| `BACKUP_PROVIDER` | sftp, s3, webdav, rclone, local | ❌ |
| `ALERT_WEBHOOK_URL` | URL Slack/Discord | ❌ |

### Sauvegardes Externes

Pour activer les sauvegardes sur un serveur distant :

```bash
# SFTP
BACKUP_PROVIDER=sftp
BACKUP_HOST=backup.example.com
BACKUP_USER=azals
BACKUP_SSH_KEY=/path/to/key

# S3 (Backblaze B2, Wasabi, MinIO)
BACKUP_PROVIDER=s3
BACKUP_S3_BUCKET=azals-backups
BACKUP_S3_ENDPOINT=https://s3.us-west-001.backblazeb2.com
BACKUP_S3_ACCESS_KEY=xxx
BACKUP_S3_SECRET_KEY=xxx

# WebDAV (Nextcloud)
BACKUP_PROVIDER=webdav
BACKUP_WEBDAV_URL=https://nextcloud.example.com/remote.php/dav/files/user/
BACKUP_WEBDAV_USER=xxx
BACKUP_WEBDAV_PASSWORD=xxx
```

## Sécurité

### Chiffrement

- **Au repos** : Toutes les données sensibles sont chiffrées avec AES-256 (Fernet)
- **Par tenant** : Chaque tenant a sa propre clé dérivée
- **En transit** : HTTPS obligatoire en production
- **Sauvegardes** : Chiffrées avant transfert

### Bonnes Pratiques

1. **Ne jamais** committer le fichier `.env`
2. **Changer** le mot de passe admin à la première connexion
3. **Configurer** HTTPS en production
4. **Activer** les sauvegardes externes
5. **Surveiller** les alertes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        NGINX                                 │
│                   (Reverse Proxy)                            │
│                    Port 80/443                               │
└─────────────────┬───────────────────┬───────────────────────┘
                  │                   │
        ┌─────────▼─────────┐  ┌─────▼─────────┐
        │     FRONTEND      │  │      API      │
        │   (React + Vite)  │  │   (FastAPI)   │
        └───────────────────┘  └───────┬───────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
      ┌───────▼───────┐       ┌───────▼───────┐       ┌────────▼────────┐
      │   PostgreSQL  │       │     Redis     │       │     Backup      │
      │   (Database)  │       │    (Cache)    │       │   (Scheduler)   │
      └───────────────┘       └───────────────┘       └─────────────────┘
```

## Maintenance

### Mise à Jour

```bash
./install.sh --upgrade
```

### Sauvegarde Manuelle

```bash
./install.sh --backup
```

### Restauration

```bash
# Lister les sauvegardes
ls backups/

# Restaurer
./install.sh --restore 2024-01-15
```

### Logs

```bash
# Tous les services
./install.sh --logs

# Service spécifique
./install.sh --logs api
```

### Statut

```bash
./install.sh --status
```

## Dépannage

### L'API ne démarre pas

1. Vérifier les logs : `./install.sh --logs api`
2. Vérifier la config : `cat .env`
3. Vérifier PostgreSQL : `docker compose exec postgres pg_isready`

### Erreur de connexion DB

1. Vérifier que PostgreSQL est démarré
2. Vérifier les credentials dans `.env`
3. Relancer : `docker compose restart`

### Problèmes de mémoire

1. Augmenter la RAM allouée à Docker
2. Réduire les limites dans `docker-compose.yml`

## Support

- **Documentation** : [docs.azalscore.com](https://docs.azalscore.com)
- **Issues** : [GitHub Issues](https://github.com/MASITH-developpement/Azalscore/issues)
- **Email** : support@azalscore.com

## Licence

AZALSCORE est un logiciel propriétaire. Voir LICENSE pour les conditions d'utilisation.
