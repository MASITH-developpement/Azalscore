#!/usr/bin/env python3
"""
AZALSCORE - Create Dashboard Mockup Image
Creates a professional-looking dashboard mockup for the landing page
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUTPUT_PATH = Path("/home/ubuntu/azalscore/frontend/public/screenshots/dashboard-mockup.png")

# Colors
DARK_BG = "#0E1420"
SIDEBAR_BG = "#1A2332"
CARD_BG = "#FFFFFF"
PRIMARY = "#1E6EFF"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
TEXT_DARK = "#1A1A2E"
TEXT_LIGHT = "#64748B"
BORDER = "#E2E8F0"

def create_mockup():
    # Image dimensions (16:10 ratio for dashboard)
    width = 1200
    height = 750

    img = Image.new('RGB', (width, height), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Try to load fonts
    try:
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_bold = font_medium = font_small = font_large = ImageFont.load_default()

    # Sidebar
    sidebar_width = 220
    draw.rectangle([(0, 0), (sidebar_width, height)], fill=SIDEBAR_BG)

    # Logo in sidebar
    draw.rectangle([(20, 20), (50, 50)], fill=PRIMARY)
    draw.text((60, 25), "AZALSCORE", fill="#FFFFFF", font=font_bold)

    # Sidebar menu items
    menu_items = [
        ("Tableau de bord", True),
        ("CRM", False),
        ("Facturation", False),
        ("Comptabilite", False),
        ("Inventaire", False),
        ("Tresorerie", False),
        ("RH & Paie", False),
        ("Rapports", False),
    ]

    y_pos = 100
    for item, active in menu_items:
        if active:
            draw.rectangle([(0, y_pos - 5), (sidebar_width, y_pos + 30)], fill=PRIMARY)
        draw.text((25, y_pos), item, fill="#FFFFFF" if active else "#94A3B8", font=font_medium)
        y_pos += 45

    # Main content area
    content_x = sidebar_width + 30
    content_y = 30
    content_width = width - sidebar_width - 60

    # Header
    draw.text((content_x, content_y), "Tableau de bord", fill="#FFFFFF", font=font_large)
    draw.text((content_x, content_y + 35), "Bienvenue ! Voici un apercu de votre activite.", fill="#94A3B8", font=font_medium)

    # Stats cards row
    card_y = content_y + 90
    card_width = (content_width - 45) // 4
    card_height = 100

    stats = [
        ("Chiffre d'affaires", "47 250 EUR", "+12.5%", SUCCESS),
        ("Factures en attente", "8", "2 500 EUR", WARNING),
        ("Nouveaux clients", "15", "+23%", SUCCESS),
        ("Devis en cours", "12", "18 400 EUR", PRIMARY),
    ]

    for i, (label, value, sub, color) in enumerate(stats):
        x = content_x + i * (card_width + 15)
        # Card background
        draw.rectangle([(x, card_y), (x + card_width, card_y + card_height)], fill=CARD_BG, outline=BORDER)
        # Card content
        draw.text((x + 15, card_y + 15), label, fill=TEXT_LIGHT, font=font_small)
        draw.text((x + 15, card_y + 35), value, fill=TEXT_DARK, font=font_bold)
        draw.text((x + 15, card_y + 65), sub, fill=color, font=font_small)

    # Chart area (left)
    chart_y = card_y + card_height + 30
    chart_width = int(content_width * 0.6)
    chart_height = 280

    draw.rectangle(
        [(content_x, chart_y), (content_x + chart_width, chart_y + chart_height)],
        fill=CARD_BG, outline=BORDER
    )
    draw.text((content_x + 20, chart_y + 15), "Evolution du CA", fill=TEXT_DARK, font=font_bold)

    # Simple bar chart
    bar_x = content_x + 40
    bar_y = chart_y + 220
    bar_width = 35
    months = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun"]
    values = [60, 80, 55, 95, 75, 110]

    for i, (month, val) in enumerate(zip(months, values)):
        x = bar_x + i * (bar_width + 25)
        bar_height = val
        # Bar
        draw.rectangle([(x, bar_y - bar_height), (x + bar_width, bar_y)], fill=PRIMARY)
        # Month label
        draw.text((x + 5, bar_y + 10), month, fill=TEXT_LIGHT, font=font_small)

    # Recent activity (right)
    activity_x = content_x + chart_width + 20
    activity_width = content_width - chart_width - 20

    draw.rectangle(
        [(activity_x, chart_y), (activity_x + activity_width, chart_y + chart_height)],
        fill=CARD_BG, outline=BORDER
    )
    draw.text((activity_x + 20, chart_y + 15), "Activite recente", fill=TEXT_DARK, font=font_bold)

    activities = [
        ("Facture #2024-156 payee", "Il y a 2h", SUCCESS),
        ("Nouveau client: Tech Solutions", "Il y a 3h", PRIMARY),
        ("Devis #2024-089 accepte", "Il y a 5h", SUCCESS),
        ("Stock faible: Produit A", "Hier", WARNING),
        ("Facture #2024-155 envoyee", "Hier", PRIMARY),
    ]

    act_y = chart_y + 55
    for text, time, color in activities:
        # Dot
        draw.ellipse([(activity_x + 20, act_y + 3), (activity_x + 28, act_y + 11)], fill=color)
        # Text
        draw.text((activity_x + 38, act_y), text[:25], fill=TEXT_DARK, font=font_small)
        draw.text((activity_x + 38, act_y + 18), time, fill=TEXT_LIGHT, font=font_small)
        act_y += 45

    # Bottom row - Quick actions and tasks
    bottom_y = chart_y + chart_height + 25
    bottom_height = height - bottom_y - 30

    # Quick actions
    qa_width = int(content_width * 0.35)
    draw.rectangle(
        [(content_x, bottom_y), (content_x + qa_width, bottom_y + bottom_height)],
        fill=CARD_BG, outline=BORDER
    )
    draw.text((content_x + 20, bottom_y + 15), "Actions rapides", fill=TEXT_DARK, font=font_bold)

    actions = ["+ Nouvelle facture", "+ Nouveau devis", "+ Nouveau client"]
    act_y = bottom_y + 50
    for action in actions:
        draw.rectangle([(content_x + 20, act_y), (content_x + qa_width - 20, act_y + 30)], fill="#EFF6FF", outline=PRIMARY)
        draw.text((content_x + 35, act_y + 7), action, fill=PRIMARY, font=font_small)
        act_y += 40

    # Tasks
    task_x = content_x + qa_width + 20
    task_width = content_width - qa_width - 20
    draw.rectangle(
        [(task_x, bottom_y), (task_x + task_width, bottom_y + bottom_height)],
        fill=CARD_BG, outline=BORDER
    )
    draw.text((task_x + 20, bottom_y + 15), "Taches du jour", fill=TEXT_DARK, font=font_bold)

    tasks = [
        ("Relancer client Dupont", False),
        ("Valider commande #456", True),
        ("Preparer rapport mensuel", False),
    ]
    task_y = bottom_y + 50
    for task, done in tasks:
        # Checkbox
        if done:
            draw.rectangle([(task_x + 20, task_y + 2), (task_x + 34, task_y + 16)], fill=SUCCESS)
        else:
            draw.rectangle([(task_x + 20, task_y + 2), (task_x + 34, task_y + 16)], outline=BORDER)
        # Task text
        color = TEXT_LIGHT if done else TEXT_DARK
        draw.text((task_x + 45, task_y), task, fill=color, font=font_small)
        task_y += 35

    # Save
    img.save(OUTPUT_PATH, quality=95, optimize=True)
    print(f"Dashboard mockup saved to {OUTPUT_PATH}")
    print(f"Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    create_mockup()
