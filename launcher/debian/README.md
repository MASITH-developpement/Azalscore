# Installation Azalscore sur Debian/Ubuntu

## Installation rapide

```bash
curl -fsSL https://raw.githubusercontent.com/MASITH-developpement/Azalscore/main/launcher/debian/install-debian.sh | bash
```

## Installation manuelle

```bash
# Cloner le depot
git clone https://github.com/MASITH-developpement/Azalscore.git ~/Azalscore

# Lancer l'installation
cd ~/Azalscore/launcher/debian
chmod +x install-debian.sh
./install-debian.sh
```

## Systemes supportes

| Distribution | Versions |
|--------------|----------|
| Debian | 10 (Buster), 11 (Bullseye), 12 (Bookworm) |
| Ubuntu | 20.04 LTS, 22.04 LTS, 24.04 LTS |
| Linux Mint | 20, 21 |
| Pop!_OS | 22.04 |

## Prerequis installes automatiquement

- Git
- Docker CE + Docker Compose Plugin
- Node.js 20 LTS
- Paquets systeme necessaires

## Apres l'installation

1. **Reconnectez-vous** ou executez `newgrp docker` pour appliquer les permissions Docker

2. **Demarrer Azalscore:**
   ```bash
   azalscore start
   # ou
   cd ~/Azalscore && ./launcher/azalscore.sh start
   ```

3. **Acceder a l'application:**
   - API Backend: http://localhost:8000
   - Documentation API: http://localhost:8000/docs
   - Frontend: http://localhost:3000

## Commandes disponibles

| Commande | Description |
|----------|-------------|
| `azalscore start` | Demarrer l'application |
| `azalscore stop` | Arreter l'application |
| `azalscore restart` | Redemarrer |
| `azalscore update` | Mettre a jour depuis GitHub |
| `azalscore logs` | Afficher les logs en temps reel |
| `azalscore status` | Etat des conteneurs Docker |
| `azalscore diagnose` | Diagnostic du systeme |

## Desinstallation

```bash
# Arreter l'application
azalscore stop

# Supprimer les conteneurs et images
cd ~/Azalscore
docker compose down -v --rmi all

# Supprimer le depot
rm -rf ~/Azalscore

# Supprimer l'alias (optionnel)
sed -i '/alias azalscore/d' ~/.bashrc
```

## Depannage

### Docker: permission denied

```bash
# Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER

# Appliquer les changements (ou reconnectez-vous)
newgrp docker
```

### Port 8000 deja utilise

```bash
# Trouver le processus
sudo lsof -i :8000

# Ou changer le port dans .env
nano ~/Azalscore/.env
# Modifier: API_PORT=8001
```

### Erreur de connexion a la base de donnees

```bash
# Verifier les logs PostgreSQL
docker compose logs db

# Recreer la base de donnees
docker compose down -v
docker compose up -d
```

## Support

- Issues: https://github.com/MASITH-developpement/Azalscore/issues
- Documentation: https://github.com/MASITH-developpement/Azalscore/tree/main/docs
