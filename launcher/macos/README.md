# Azalscore Launcher pour macOS

Ce dossier contient les scripts et l'application pour installer, mettre à jour et lancer Azalscore sur macOS (MacBook Air, MacBook Pro, iMac, etc.).

## Fonctionnalités

- **Installation automatique** : Clone le dépôt GitHub lors du premier lancement
- **Mise à jour automatique** : Synchronise avec la branche `main` à chaque démarrage
- **Gestion Docker** : Démarre automatiquement Docker Desktop si nécessaire
- **Configuration automatique** : Génère les clés secrètes et configure l'environnement
- **Application native** : Azalscore.app pour le Launchpad et le Dock

## Prérequis

Les outils suivants sont nécessaires :

- **macOS** 10.13 ou supérieur
- **Docker Desktop** pour Mac
- **Git**
- **Node.js** >= 18 (optionnel, pour le développement frontend)

## Installation rapide

### 1. Télécharger les scripts

```bash
# Cloner le dépôt
git clone https://github.com/MASITH-developpement/Azalscore.git
cd Azalscore/launcher/macos
```

### 2. Installer les prérequis

```bash
chmod +x install-prerequisites.sh
./install-prerequisites.sh
```

Ce script installe automatiquement :
- Xcode Command Line Tools
- Homebrew
- Git
- Docker Desktop
- Node.js LTS

### 3. Lancer Azalscore

```bash
chmod +x azalscore-launcher.sh
./azalscore-launcher.sh
```

## Créer l'application macOS

Pour créer une application .app que vous pouvez ajouter au Dock :

```bash
chmod +x create-app.sh
./create-app.sh
```

Ce script :
1. Configure l'application Azalscore.app
2. Propose de l'installer dans `/Applications`
3. Propose de l'ajouter au Dock

## Utilisation

### Commandes disponibles

```bash
# Démarrer Azalscore (mise à jour + lancement)
./azalscore-launcher.sh start

# Arrêter Azalscore
./azalscore-launcher.sh stop

# Redémarrer Azalscore
./azalscore-launcher.sh restart

# Mettre à jour sans redémarrer
./azalscore-launcher.sh update

# Voir les logs
./azalscore-launcher.sh logs

# Voir l'état des conteneurs
./azalscore-launcher.sh status

# Lancer le frontend en mode dev
./azalscore-launcher.sh frontend

# Afficher l'aide
./azalscore-launcher.sh help
```

### Avec l'application .app

1. Double-cliquez sur **Azalscore.app** dans le Finder ou le Launchpad
2. Un terminal s'ouvre et lance automatiquement Azalscore
3. L'application se met à jour depuis GitHub avant chaque démarrage

## URLs d'accès

Une fois l'application démarrée :

| Service | URL |
|---------|-----|
| API Backend | http://localhost:8000 |
| Documentation API | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Frontend | http://localhost:3000 |

## Structure des fichiers

```
launcher/macos/
├── README.md                    # Ce fichier
├── azalscore-launcher.sh        # Script principal de lancement
├── install-prerequisites.sh     # Installation des dépendances
├── create-app.sh                # Création de l'application .app
└── Azalscore.app/               # Application macOS
    └── Contents/
        ├── Info.plist           # Métadonnées de l'app
        ├── MacOS/
        │   └── Azalscore        # Script exécutable
        └── Resources/
            └── AppIcon.icns     # Icône (générée par create-app.sh)
```

## Configuration

### Emplacement des fichiers

- **Dépôt cloné** : `~/Azalscore`
- **Logs du launcher** : `~/.azalscore/launcher.log`
- **Logs du frontend** : `~/.azalscore/frontend.log`
- **Scripts installés** : `~/.azalscore/scripts/`

### Variables d'environnement

Le fichier `.env` est automatiquement créé lors du premier lancement avec des clés sécurisées. Vous pouvez le modifier dans `~/Azalscore/.env`.

## Dépannage

### Docker ne démarre pas

1. Ouvrez Docker Desktop manuellement
2. Attendez que l'icône Docker arrête de clignoter
3. Relancez le script

### Erreur de permissions

```bash
chmod +x azalscore-launcher.sh
chmod +x install-prerequisites.sh
chmod +x create-app.sh
```

### L'API ne répond pas

```bash
# Vérifier les logs
cd ~/Azalscore
docker compose logs -f

# Redémarrer les conteneurs
docker compose down
docker compose up --build -d
```

### Réinitialisation complète

```bash
# Arrêter et supprimer les conteneurs
cd ~/Azalscore
docker compose down -v

# Supprimer la base de données
docker volume rm azalscore_postgres_data

# Relancer
./launcher/macos/azalscore-launcher.sh
```

## Mise à jour manuelle

Pour forcer une mise à jour depuis GitHub :

```bash
cd ~/Azalscore
git fetch origin main
git reset --hard origin/main
docker compose up --build -d
```

## Support

Pour signaler un problème ou demander de l'aide :
- GitHub Issues : https://github.com/MASITH-developpement/Azalscore/issues
