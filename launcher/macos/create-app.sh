#!/bin/bash
#
# Script pour créer l'application Azalscore.app sur macOS
# Ce script génère une icône et configure l'application
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Azalscore"
APP_PATH="$SCRIPT_DIR/$APP_NAME.app"
INSTALL_PATH="/Applications/$APP_NAME.app"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       Création de l'application Azalscore.app                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Créer la structure de l'application si elle n'existe pas
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Rendre le script exécutable
chmod +x "$APP_PATH/Contents/MacOS/Azalscore"

# Créer une icône simple (SVG vers icône)
create_icon() {
    echo -e "${BLUE}Création de l'icône de l'application...${NC}"

    # Créer un fichier SVG temporaire pour l'icône
    cat > /tmp/azalscore_icon.svg << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4F46E5"/>
      <stop offset="100%" style="stop-color:#7C3AED"/>
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="220" fill="url(#bg)"/>
  <text x="512" y="620" text-anchor="middle" fill="white" font-family="SF Pro Display, -apple-system, sans-serif" font-weight="bold" font-size="400">A</text>
  <circle cx="512" cy="280" r="80" fill="white" opacity="0.9"/>
</svg>
SVGEOF

    # Vérifier si on peut créer l'icône
    if command -v sips &> /dev/null && command -v iconutil &> /dev/null; then
        # Créer le dossier iconset
        mkdir -p /tmp/AppIcon.iconset

        # Convertir SVG en PNG avec différentes tailles (nécessite un outil de conversion)
        # Pour simplifier, on crée une image placeholder
        for size in 16 32 64 128 256 512; do
            # Créer un PNG simple avec sips (on utilise une image de base)
            if [ -f "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns" ]; then
                sips -s format png -z $size $size "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns" --out "/tmp/AppIcon.iconset/icon_${size}x${size}.png" 2>/dev/null || true
                sips -s format png -z $((size*2)) $((size*2)) "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns" --out "/tmp/AppIcon.iconset/icon_${size}x${size}@2x.png" 2>/dev/null || true
            fi
        done

        # Créer l'icns
        if [ -d "/tmp/AppIcon.iconset" ] && [ "$(ls -A /tmp/AppIcon.iconset)" ]; then
            iconutil -c icns /tmp/AppIcon.iconset -o "$APP_PATH/Contents/Resources/AppIcon.icns" 2>/dev/null && \
            echo -e "${GREEN}✓ Icône créée${NC}" || \
            echo -e "${YELLOW}⚠ Utilisation de l'icône par défaut${NC}"
        fi

        # Nettoyer
        rm -rf /tmp/AppIcon.iconset /tmp/azalscore_icon.svg
    else
        echo -e "${YELLOW}⚠ Impossible de créer l'icône personnalisée, utilisation de l'icône par défaut${NC}"
    fi
}

# Copier le script de lancement dans l'application
setup_launcher() {
    echo -e "${BLUE}Configuration du lanceur...${NC}"

    # S'assurer que le script principal est exécutable
    chmod +x "$SCRIPT_DIR/azalscore-launcher.sh"
    chmod +x "$SCRIPT_DIR/install-prerequisites.sh"
    chmod +x "$APP_PATH/Contents/MacOS/Azalscore"

    echo -e "${GREEN}✓ Scripts configurés${NC}"
}

# Installer l'application dans /Applications
install_app() {
    echo ""
    echo -e "${YELLOW}Voulez-vous installer Azalscore dans le dossier Applications? (o/n)${NC}"
    read -r response

    if [[ "$response" =~ ^[OoYy]$ ]]; then
        if [ -d "$INSTALL_PATH" ]; then
            echo -e "${YELLOW}Une version existante a été trouvée. Remplacement...${NC}"
            rm -rf "$INSTALL_PATH"
        fi

        # Copier l'application et les scripts
        mkdir -p "$INSTALL_PATH"
        cp -R "$APP_PATH/"* "$INSTALL_PATH/"

        # Copier les scripts de lancement à côté de l'app pour référence
        mkdir -p "$HOME/.azalscore/scripts"
        cp "$SCRIPT_DIR/azalscore-launcher.sh" "$HOME/.azalscore/scripts/"
        cp "$SCRIPT_DIR/install-prerequisites.sh" "$HOME/.azalscore/scripts/"

        # Mettre à jour le chemin dans le script de l'app
        cat > "$INSTALL_PATH/Contents/MacOS/Azalscore" << 'LAUNCHER'
#!/bin/bash
LAUNCHER_SCRIPT="$HOME/.azalscore/scripts/azalscore-launcher.sh"

if [ ! -f "$LAUNCHER_SCRIPT" ]; then
    osascript -e 'display alert "Erreur" message "Script de lancement non trouvé. Veuillez réinstaller Azalscore." as critical'
    exit 1
fi

chmod +x "$LAUNCHER_SCRIPT"

osascript <<EOF
tell application "Terminal"
    activate
    do script "\"$LAUNCHER_SCRIPT\" start"
end tell
EOF
LAUNCHER
        chmod +x "$INSTALL_PATH/Contents/MacOS/Azalscore"

        echo -e "${GREEN}✓ Azalscore installé dans /Applications${NC}"
        echo -e "${GREEN}✓ Vous pouvez maintenant le lancer depuis le Launchpad ou le Finder${NC}"
    else
        echo -e "${BLUE}Installation annulée. Vous pouvez exécuter l'app depuis: $APP_PATH${NC}"
    fi
}

# Créer un raccourci dans le Dock (optionnel)
add_to_dock() {
    echo ""
    echo -e "${YELLOW}Voulez-vous ajouter Azalscore au Dock? (o/n)${NC}"
    read -r response

    if [[ "$response" =~ ^[OoYy]$ ]]; then
        if [ -d "$INSTALL_PATH" ]; then
            defaults write com.apple.dock persistent-apps -array-add "<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>$INSTALL_PATH</string><key>_CFURLStringType</key><integer>0</integer></dict></dict></dict>"
            killall Dock
            echo -e "${GREEN}✓ Azalscore ajouté au Dock${NC}"
        else
            echo -e "${YELLOW}⚠ Installez d'abord l'application dans /Applications${NC}"
        fi
    fi
}

# Menu principal
main() {
    create_icon
    setup_launcher

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}            Application Azalscore.app créée!                    ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Emplacement: $APP_PATH${NC}"
    echo ""

    install_app
    add_to_dock

    echo ""
    echo -e "${CYAN}Pour lancer Azalscore:${NC}"
    echo "  - Double-cliquez sur Azalscore.app"
    echo "  - Ou utilisez le terminal: ./azalscore-launcher.sh"
    echo ""
}

main "$@"
