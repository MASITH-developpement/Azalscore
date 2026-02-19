#!/usr/bin/env python3
"""
AZALSCORE - Generateur d'images Open Graph et Twitter
Conforme a la charte graphique AZALSCORE
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Charte AZALSCORE
COLORS = {
    'primary': (30, 110, 255),      # #1E6EFF - Bleu AZALSCORE
    'dark': (14, 20, 32),           # #0E1420 - Bleu Nuit
    'white': (255, 255, 255),       # #FFFFFF
    'gradient_end': (79, 195, 255), # #4FC3FF - Fin du degrade
}

# Dimensions standard
OG_SIZE = (1200, 630)    # Facebook/LinkedIn
TWITTER_SIZE = (1200, 600)  # Twitter (2:1 ratio)


def create_gradient_background(size, color_start, color_end):
    """Cree un fond avec degrade vertical"""
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)

    for y in range(size[1]):
        ratio = y / size[1]
        r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
        g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
        b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))

    return img


def draw_logo(draw, x, y, size=80):
    """Dessine le logo AZALSCORE simplifie"""
    # Rectangle arrondi (simplifie en rectangle)
    margin = size // 10
    draw.rectangle(
        [x, y, x + size, y + size],
        fill=COLORS['primary']
    )

    # Lettre A stylisee
    a_margin = size // 5
    ax, ay = x + a_margin, y + a_margin
    a_size = size - (a_margin * 2)

    # Triangle pour le A
    points = [
        (ax + a_size // 2, ay),           # Sommet
        (ax, ay + a_size),                 # Bas gauche
        (ax + a_size, ay + a_size),        # Bas droit
    ]
    draw.polygon(points, fill=COLORS['white'])

    # Cercle du A
    circle_size = a_size // 4
    cx = ax + a_size // 2 - circle_size // 2
    cy = ay + a_size - circle_size - (a_size // 10)
    draw.ellipse([cx, cy, cx + circle_size, cy + circle_size], fill=COLORS['dark'])


def generate_og_image(output_path, size=OG_SIZE):
    """Genere l'image Open Graph principale"""
    # Creer le fond avec degrade subtil
    img = create_gradient_background(size, COLORS['dark'], (20, 30, 50))
    draw = ImageDraw.Draw(img)

    # Logo
    logo_size = 100
    logo_x = 80
    logo_y = (size[1] - logo_size) // 2 - 50
    draw_logo(draw, logo_x, logo_y, logo_size)

    # Textes (sans police custom, utiliser default)
    # Titre AZALSCORE
    title_y = logo_y + logo_size + 30
    draw.text(
        (logo_x, title_y),
        "AZALSCORE",
        fill=COLORS['white']
    )

    # Tagline
    tagline_y = title_y + 40
    tagline = "L'ERP complet pour les PME modernes"
    draw.text(
        (logo_x, tagline_y),
        tagline,
        fill=COLORS['primary']
    )

    # Description
    desc_y = tagline_y + 35
    description = "CRM | Facturation | Comptabilite | Stock | RH | Tresorerie"
    draw.text(
        (logo_x, desc_y),
        description,
        fill=(180, 180, 200)
    )

    # Badge "100% Francais"
    badge_x = size[0] - 200
    badge_y = size[1] - 80
    draw.rectangle(
        [badge_x, badge_y, badge_x + 150, badge_y + 40],
        fill=COLORS['primary']
    )
    draw.text(
        (badge_x + 20, badge_y + 10),
        "100% Francais",
        fill=COLORS['white']
    )

    # Bande decorative en bas
    stripe_height = 8
    draw.rectangle(
        [0, size[1] - stripe_height, size[0], size[1]],
        fill=COLORS['primary']
    )

    # Accent degrade sur le cote droit
    for x in range(size[0] - 300, size[0]):
        ratio = (x - (size[0] - 300)) / 300
        alpha = int(ratio * 100)
        r = int(COLORS['primary'][0] * ratio)
        g = int(COLORS['primary'][1] * ratio)
        b = int(COLORS['primary'][2] * ratio)
        if alpha > 0:
            draw.line([(x, 0), (x, size[1] - stripe_height)], fill=(r, g, b, alpha))

    # Sauvegarder
    img.save(output_path, 'PNG', optimize=True)
    print(f"Image generee: {output_path}")
    return img


def main():
    """Point d'entree principal"""
    output_dir = "/home/ubuntu/azalscore/frontend/public"

    # Generer image OG (Facebook, LinkedIn)
    og_path = os.path.join(output_dir, "og-image.png")
    generate_og_image(og_path, OG_SIZE)

    # Generer image Twitter (meme contenu, ratio different)
    twitter_path = os.path.join(output_dir, "twitter-image.png")
    generate_og_image(twitter_path, TWITTER_SIZE)

    print(f"\nImages generees avec succes dans {output_dir}")
    print("- og-image.png (1200x630)")
    print("- twitter-image.png (1200x600)")


if __name__ == "__main__":
    main()
