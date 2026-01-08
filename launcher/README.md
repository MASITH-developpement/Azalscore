# Azalscore - Launcher Universel

Programme d'installation et de lancement automatique pour Azalscore, compatible avec tous les systèmes d'exploitation.

## Systèmes supportés

| OS | Version | Architecture |
|----|---------|--------------|
| **macOS** | 10.13+ (High Sierra, Mojave, Catalina, Big Sur, Monterey, Ventura, Sonoma) | Intel (x86_64), Apple Silicon (arm64) |
| **Linux** | Ubuntu 18.04+, Debian 10+, Fedora 35+, CentOS 8+, Arch, openSUSE, Alpine | x86_64, arm64 |
| **Windows** | 10 (1903+), 11 | x86_64 |

## Installation rapide

### macOS / Linux

```bash
# Télécharger et exécuter
curl -fsSL https://raw.githubusercontent.com/MASITH-developpement/Azalscore/main/launcher/install.sh | bash

# Puis lancer
~/Azalscore/launcher/azalscore.sh
```

Ou manuellement :

```bash
git clone https://github.com/MASITH-developpement/Azalscore.git ~/Azalscore
cd ~/Azalscore/launcher
./install.sh
./azalscore.sh
```

### Windows

```powershell
# Dans PowerShell (Admin)
git clone https://github.com/MASITH-developpement/Azalscore.git $env:USERPROFILE\Azalscore
cd $env:USERPROFILE\Azalscore\launcher\windows
.\azalscore.ps1
```

## Fonctionnalités

### Détection automatique du système

Le launcher détecte automatiquement :
- **Type d'OS** : macOS, Linux, Windows
- **Version** : macOS Monterey, Ubuntu 22.04, Windows 11, etc.
- **Architecture** : Intel (x86_64), Apple Silicon (arm64), ARM
- **Gestionnaire de paquets** : Homebrew, apt, dnf, yum, pacman, zypper, apk, winget, chocolatey

### Installation des prérequis

Les dépendances sont installées automatiquement selon l'OS :

| Prérequis | macOS | Linux | Windows |
|-----------|-------|-------|---------|
| Git | Homebrew | apt/dnf/yum/pacman | winget/choco |
| Docker | Docker Desktop (DMG) | docker-ce (repo officiel) | Docker Desktop (winget) |
| Docker Compose | Inclus dans Docker Desktop | Plugin Docker | Inclus dans Docker Desktop |
| Node.js | Homebrew | NodeSource | winget/choco |

### Mise à jour automatique

À chaque lancement, le script :
1. Synchronise avec la branche `main` de GitHub
2. Préserve vos modifications locales (git stash)
3. Régénère l'environnement si nécessaire

## Commandes disponibles

### macOS / Linux

```bash
./azalscore.sh start      # Démarrer (par défaut)
./azalscore.sh stop       # Arrêter
./azalscore.sh restart    # Redémarrer
./azalscore.sh update     # Mettre à jour sans redémarrer
./azalscore.sh logs       # Voir les logs
./azalscore.sh status     # État des conteneurs
./azalscore.sh install    # Installer les prérequis
./azalscore.sh diagnose   # Diagnostic système
./azalscore.sh help       # Aide
```

### Windows (PowerShell)

```powershell
.\azalscore.ps1 start
.\azalscore.ps1 stop
.\azalscore.ps1 restart
.\azalscore.ps1 update
.\azalscore.ps1 logs
.\azalscore.ps1 status
.\azalscore.ps1 install
.\azalscore.ps1 diagnose
.\azalscore.ps1 help
```

## Structure des fichiers

```
launcher/
├── README.md              # Ce fichier
├── install.sh             # Script d'installation universel (macOS/Linux)
├── azalscore.sh           # Launcher universel (macOS/Linux)
├── macos/
│   ├── azalscore-launcher.sh    # Launcher spécifique macOS
│   ├── install-prerequisites.sh # Installation prérequis macOS
│   ├── create-app.sh            # Création de l'app .app
│   ├── Azalscore.app/           # Application macOS
│   └── README.md
├── linux/
│   └── (scripts spécifiques Linux si nécessaire)
└── windows/
    └── azalscore.ps1      # Launcher PowerShell pour Windows
```

## Diagnostic système

Le launcher inclut un diagnostic complet :

```bash
./azalscore.sh diagnose
```

Affiche :
- Système d'exploitation et version
- Architecture CPU
- RAM et espace disque
- Logiciels installés (Git, Docker, Node.js)
- État de l'installation Azalscore

## URLs d'accès

Une fois lancé :

| Service | URL |
|---------|-----|
| API Backend | http://localhost:8000 |
| Documentation API | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Frontend (dev) | http://localhost:3000 |

## Configuration

### Fichier .env

Créé automatiquement avec des clés sécurisées lors du premier lancement.
Emplacement : `~/Azalscore/.env`

### Logs

| Fichier | Description |
|---------|-------------|
| `~/.azalscore/launcher.log` | Logs du launcher |
| `docker compose logs` | Logs des conteneurs |

## Dépannage

### Docker ne démarre pas

**macOS** : Ouvrez Docker Desktop manuellement depuis Applications

**Linux** :
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

**Windows** : Lancez Docker Desktop depuis le menu Démarrer

### Erreur de permissions (Linux)

```bash
sudo usermod -aG docker $USER
# Déconnectez-vous et reconnectez-vous
```

### Réinitialisation complète

```bash
cd ~/Azalscore
docker compose down -v
rm -rf ~/Azalscore
# Relancez l'installation
```

## Support

- GitHub Issues : https://github.com/MASITH-developpement/Azalscore/issues
