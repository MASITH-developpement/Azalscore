#!/usr/bin/env python3
"""
AZALSCORE - Capture Interface Screenshots
Capture des screenshots professionnels de l'interface pour le marketing
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "https://azalscore.com"
LOGIN_TENANT = "masith"
LOGIN_EMAIL = "contact@masith.fr"
LOGIN_PASSWORD = "Gobelet2026!"
OUTPUT_DIR = Path("/home/ubuntu/azalscore/frontend/public/screenshots")

# Pages à capturer après login
PAGES_TO_CAPTURE = [
    {
        "name": "cockpit",
        "url": "/cockpit",
        "title": "Tableau de Bord",
        "wait_for": "text=Bienvenue"
    },
    {
        "name": "crm-contacts",
        "url": "/crm/contacts",
        "title": "CRM - Contacts",
        "wait_for": "text=Contact"
    },
    {
        "name": "commercial-devis",
        "url": "/commercial/documents?type=quote",
        "title": "Devis",
        "wait_for": "text=Devis"
    },
    {
        "name": "commercial-factures",
        "url": "/commercial/documents?type=invoice",
        "title": "Factures",
        "wait_for": "text=Factur"
    },
    {
        "name": "tresorerie",
        "url": "/tresorerie",
        "title": "Tresorerie",
        "wait_for": "text=Tresorerie"
    },
    {
        "name": "inventaire",
        "url": "/inventaire",
        "title": "Inventaire",
        "wait_for": "text=Inventaire"
    },
]


def capture_screenshots():
    """Capture tous les screenshots de l'interface"""
    from playwright.sync_api import sync_playwright

    # Créer le dossier de sortie
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Demarrage de la capture...")

    with sync_playwright() as p:
        # Lancer le navigateur
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,  # Retina quality
            locale='fr-FR'
        )

        page = context.new_page()

        try:
            # 1. Aller sur la page de login
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Navigation vers {BASE_URL}/login")
            page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Screenshot de la page de login
            page.screenshot(
                path=str(OUTPUT_DIR / "login.png"),
                full_page=False
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Screenshot login.png sauvegarde")

            # 2. Se connecter
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connexion avec {LOGIN_TENANT}/{LOGIN_EMAIL}...")

            # Remplir le formulaire de login (3 champs: Societe, Email, Mot de passe)
            # Champ 1: Societe (tenant ID)
            tenant_input = page.locator('input[placeholder*="identifiant-societe" i], input[name="tenant"], input[name="company"]')
            if tenant_input.count() > 0:
                tenant_input.first.fill(LOGIN_TENANT)
            else:
                # Premier input texte qui n'est pas email/password
                page.locator('input[type="text"]').first.fill(LOGIN_TENANT)

            page.wait_for_timeout(500)

            # Champ 2: Email
            email_input = page.locator('input[type="email"], input[name="email"], input#email, input[placeholder*="email" i]')
            if email_input.count() > 0:
                email_input.first.fill(LOGIN_EMAIL)

            page.wait_for_timeout(500)

            # Champ 3: Mot de passe
            password_input = page.locator('input[type="password"], input[name="password"], input#password')
            if password_input.count() > 0:
                password_input.first.fill(LOGIN_PASSWORD)

            page.wait_for_timeout(500)

            # Screenshot avant soumission pour debug
            page.screenshot(path=str(OUTPUT_DIR / "pre-submit.png"))

            # Cliquer sur le bouton de connexion
            submit_btn = page.locator('button[type="submit"], button:has-text("Connexion"), button:has-text("Se connecter")')
            submit_btn.first.click()

            # Attendre un peu pour voir la reponse
            page.wait_for_timeout(3000)

            # Screenshot apres soumission pour debug
            page.screenshot(path=str(OUTPUT_DIR / "post-submit.png"))

            # Verifier si on est redirige vers cockpit ou s'il y a une erreur
            current_url = page.url
            print(f"[{datetime.now().strftime('%H:%M:%S')}] URL apres login: {current_url}")

            if "/cockpit" in current_url:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connexion reussie!")
            else:
                # Attendre plus longtemps pour la redirection
                try:
                    page.wait_for_url("**/cockpit**", timeout=15000)
                    page.wait_for_load_state("networkidle")
                except:
                    # Peut-etre deja sur la bonne page mais URL differente
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tentative de navigation directe vers cockpit...")
                    page.goto(f"{BASE_URL}/cockpit", wait_until="networkidle", timeout=30000)

            page.wait_for_timeout(2000)  # Attendre les animations
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Navigation cockpit terminee")

            # 3. Capturer chaque page
            for page_info in PAGES_TO_CAPTURE:
                try:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Capture {page_info['name']}...")

                    page.goto(f"{BASE_URL}{page_info['url']}", wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(2000)  # Attendre les animations

                    # Screenshot complet
                    page.screenshot(
                        path=str(OUTPUT_DIR / f"{page_info['name']}.png"),
                        full_page=False
                    )
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   -> {page_info['name']}.png sauvegarde")

                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Erreur sur {page_info['name']}: {e}")

            # 4. Capturer aussi la landing page
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Capture de la landing page...")
            page.goto(f"{BASE_URL}/", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            page.screenshot(
                path=str(OUTPUT_DIR / "landing.png"),
                full_page=False
            )
            page.screenshot(
                path=str(OUTPUT_DIR / "landing-full.png"),
                full_page=True
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   -> landing.png et landing-full.png sauvegardes")

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERREUR: {e}")
            # Capturer l'état actuel pour debug
            page.screenshot(path=str(OUTPUT_DIR / "error-state.png"))
            raise
        finally:
            browser.close()

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Capture terminee!")
    print(f"Screenshots sauvegardes dans: {OUTPUT_DIR}")

    # Lister les fichiers générés
    for f in sorted(OUTPUT_DIR.glob("*.png")):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")


def generate_og_images():
    """Génère les images OG à partir des screenshots"""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generation des images OG...")

    # Dimensions OG standard
    OG_WIDTH = 1200
    OG_HEIGHT = 630

    # Charger le screenshot de la landing page (meilleur pour le marketing)
    landing_path = OUTPUT_DIR / "landing.png"
    if not landing_path.exists():
        print("Erreur: landing.png non trouve, utilisation du cockpit")
        landing_path = OUTPUT_DIR / "cockpit.png"

    if not landing_path.exists():
        print("Erreur: Aucun screenshot trouve!")
        return

    screenshot = Image.open(landing_path)

    # Créer l'image OG
    og_image = Image.new('RGB', (OG_WIDTH, OG_HEIGHT), '#0E1420')

    # Redimensionner le screenshot pour qu'il tienne dans l'image
    # On prend 70% de la largeur pour le screenshot
    screenshot_width = int(OG_WIDTH * 0.7)
    screenshot_height = int(screenshot_width * screenshot.height / screenshot.width)

    if screenshot_height > OG_HEIGHT - 60:
        screenshot_height = OG_HEIGHT - 60
        screenshot_width = int(screenshot_height * screenshot.width / screenshot.height)

    screenshot_resized = screenshot.resize(
        (screenshot_width, screenshot_height),
        Image.Resampling.LANCZOS
    )

    # Appliquer un léger arrondi/ombre
    # Position du screenshot (droite de l'image)
    x_offset = OG_WIDTH - screenshot_width - 30
    y_offset = (OG_HEIGHT - screenshot_height) // 2

    # Coller le screenshot
    og_image.paste(screenshot_resized, (x_offset, y_offset))

    # Ajouter le texte à gauche
    draw = ImageDraw.Draw(og_image)

    # Essayer de charger une police
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # Zone de texte à gauche
    text_x = 40
    text_y = 150

    # Logo/Nom
    draw.text((text_x, text_y), "AZALSCORE", fill='#1E6EFF', font=font_large)

    # Tagline
    draw.text((text_x, text_y + 70), "ERP SaaS Francais", fill='#FFFFFF', font=font_medium)
    draw.text((text_x, text_y + 100), "pour PME", fill='#FFFFFF', font=font_medium)

    # Features
    features = [
        "CRM & Gestion Commerciale",
        "Facturation & Comptabilite",
        "Inventaire & Logistique",
        "RH & Paie"
    ]

    feature_y = text_y + 160
    for feature in features:
        draw.text((text_x, feature_y), f"• {feature}", fill='#94A3B8', font=font_small)
        feature_y += 30

    # CTA
    draw.text((text_x, OG_HEIGHT - 100), "Essai Gratuit 30 Jours", fill='#22C55E', font=font_medium)
    draw.text((text_x, OG_HEIGHT - 65), "azalscore.com", fill='#64748B', font=font_small)

    # Sauvegarder
    og_output = Path("/home/ubuntu/azalscore/frontend/public/og-image.png")
    og_image.save(og_output, quality=95, optimize=True)
    print(f"  -> og-image.png sauvegarde ({og_output.stat().st_size / 1024:.1f} KB)")

    # Twitter image (1200x600)
    twitter_image = og_image.crop((0, 15, 1200, 615))
    twitter_output = Path("/home/ubuntu/azalscore/frontend/public/twitter-image.png")
    twitter_image.save(twitter_output, quality=95, optimize=True)
    print(f"  -> twitter-image.png sauvegarde ({twitter_output.stat().st_size / 1024:.1f} KB)")

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Images OG generees avec succes!")


if __name__ == "__main__":
    try:
        capture_screenshots()
        generate_og_images()
    except Exception as e:
        print(f"ERREUR FATALE: {e}")
        sys.exit(1)
