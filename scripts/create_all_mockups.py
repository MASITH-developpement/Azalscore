#!/usr/bin/env python3
"""
AZALSCORE - Create All Mockup Images
Generates professional mockups for each slide of the demo
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUTPUT_DIR = Path("/home/ubuntu/azalscore/frontend/public/screenshots")

# Colors
DARK_BG = "#0E1420"
SIDEBAR_BG = "#1A2332"
CARD_BG = "#FFFFFF"
PRIMARY = "#1E6EFF"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
DANGER = "#EF4444"
TEXT_DARK = "#1A1A2E"
TEXT_LIGHT = "#64748B"
BORDER = "#E2E8F0"

# Fonts
try:
    FONT_BOLD = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    FONT_XLARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
except:
    FONT_BOLD = FONT_MEDIUM = FONT_SMALL = FONT_LARGE = FONT_XLARGE = ImageFont.load_default()


def draw_sidebar(draw, width, height, active_menu):
    """Draw the sidebar with menu items"""
    sidebar_width = 220
    draw.rectangle([(0, 0), (sidebar_width, height)], fill=SIDEBAR_BG)

    # Logo
    draw.rectangle([(20, 20), (50, 50)], fill=PRIMARY)
    draw.text((60, 25), "AZALSCORE", fill="#FFFFFF", font=FONT_BOLD)

    # Menu items
    menu_items = [
        "Tableau de bord",
        "CRM",
        "Facturation",
        "Comptabilite",
        "Inventaire",
        "Tresorerie",
        "RH & Paie",
        "Rapports",
    ]

    y_pos = 100
    for item in menu_items:
        is_active = item == active_menu
        if is_active:
            draw.rectangle([(0, y_pos - 5), (sidebar_width, y_pos + 30)], fill=PRIMARY)
        draw.text((25, y_pos), item, fill="#FFFFFF" if is_active else "#94A3B8", font=FONT_MEDIUM)
        y_pos += 45

    return sidebar_width


def create_dashboard_mockup():
    """Slide 1: Tableau de bord"""
    width, height = 1200, 750
    img = Image.new('RGB', (width, height), DARK_BG)
    draw = ImageDraw.Draw(img)

    sidebar_width = draw_sidebar(draw, width, height, "Tableau de bord")
    content_x = sidebar_width + 30

    # Header
    draw.text((content_x, 30), "Tableau de bord", fill="#FFFFFF", font=FONT_LARGE)
    draw.text((content_x, 65), "Bienvenue ! Voici un apercu de votre activite.", fill="#94A3B8", font=FONT_MEDIUM)

    # Stats cards
    card_y = 110
    card_width = 220
    card_height = 100
    stats = [
        ("Chiffre d'affaires", "47 250 EUR", "+12.5%", SUCCESS),
        ("Factures en attente", "8", "2 500 EUR", WARNING),
        ("Nouveaux clients", "15", "+23%", SUCCESS),
        ("Devis en cours", "12", "18 400 EUR", PRIMARY),
    ]

    for i, (label, value, sub, color) in enumerate(stats):
        x = content_x + i * (card_width + 15)
        draw.rectangle([(x, card_y), (x + card_width, card_y + card_height)], fill=CARD_BG, outline=BORDER)
        draw.text((x + 15, card_y + 15), label, fill=TEXT_LIGHT, font=FONT_SMALL)
        draw.text((x + 15, card_y + 35), value, fill=TEXT_DARK, font=FONT_BOLD)
        draw.text((x + 15, card_y + 65), sub, fill=color, font=FONT_SMALL)

    # Chart
    chart_y = card_y + card_height + 25
    chart_width = 580
    chart_height = 280
    draw.rectangle([(content_x, chart_y), (content_x + chart_width, chart_y + chart_height)], fill=CARD_BG, outline=BORDER)
    draw.text((content_x + 20, chart_y + 15), "Evolution du CA", fill=TEXT_DARK, font=FONT_BOLD)

    # Bar chart
    bar_x = content_x + 40
    bar_y = chart_y + 220
    bar_width = 35
    months = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun"]
    values = [60, 80, 55, 95, 75, 110]
    for i, (month, val) in enumerate(zip(months, values)):
        x = bar_x + i * (bar_width + 25)
        draw.rectangle([(x, bar_y - val), (x + bar_width, bar_y)], fill=PRIMARY)
        draw.text((x + 5, bar_y + 10), month, fill=TEXT_LIGHT, font=FONT_SMALL)

    # Activity
    activity_x = content_x + chart_width + 20
    activity_width = 320
    draw.rectangle([(activity_x, chart_y), (activity_x + activity_width, chart_y + chart_height)], fill=CARD_BG, outline=BORDER)
    draw.text((activity_x + 20, chart_y + 15), "Activite recente", fill=TEXT_DARK, font=FONT_BOLD)

    activities = [
        ("Facture #2024-156 payee", "Il y a 2h", SUCCESS),
        ("Nouveau client: Tech Sol", "Il y a 3h", PRIMARY),
        ("Devis #2024-089 accepte", "Il y a 5h", SUCCESS),
        ("Stock faible: Produit A", "Hier", WARNING),
    ]
    act_y = chart_y + 55
    for text, time, color in activities:
        draw.ellipse([(activity_x + 20, act_y + 3), (activity_x + 28, act_y + 11)], fill=color)
        draw.text((activity_x + 38, act_y), text[:22], fill=TEXT_DARK, font=FONT_SMALL)
        draw.text((activity_x + 38, act_y + 18), time, fill=TEXT_LIGHT, font=FONT_SMALL)
        act_y += 45

    img.save(OUTPUT_DIR / "mockup-dashboard.png", quality=95)
    print("Created: mockup-dashboard.png")


def create_commercial_mockup():
    """Slide 2: Gestion commerciale - Factures"""
    width, height = 1200, 750
    img = Image.new('RGB', (width, height), DARK_BG)
    draw = ImageDraw.Draw(img)

    sidebar_width = draw_sidebar(draw, width, height, "Facturation")
    content_x = sidebar_width + 30
    content_width = width - sidebar_width - 60

    # Header
    draw.text((content_x, 30), "Facturation", fill="#FFFFFF", font=FONT_LARGE)

    # Action buttons
    btn_y = 75
    draw.rectangle([(content_x, btn_y), (content_x + 140, btn_y + 36)], fill=PRIMARY)
    draw.text((content_x + 15, btn_y + 10), "+ Nouvelle facture", fill="#FFFFFF", font=FONT_SMALL)
    draw.rectangle([(content_x + 155, btn_y), (content_x + 280, btn_y + 36)], fill="#2D3748", outline=PRIMARY)
    draw.text((content_x + 170, btn_y + 10), "+ Nouveau devis", fill=PRIMARY, font=FONT_SMALL)

    # Stats row
    stats_y = 130
    mini_stats = [("12", "Factures ce mois"), ("8 450 EUR", "En attente"), ("45 200 EUR", "Encaisse")]
    stat_width = 180
    for i, (val, label) in enumerate(mini_stats):
        x = content_x + i * (stat_width + 20)
        draw.rectangle([(x, stats_y), (x + stat_width, stats_y + 70)], fill=CARD_BG, outline=BORDER)
        draw.text((x + 15, stats_y + 12), val, fill=PRIMARY, font=FONT_BOLD)
        draw.text((x + 15, stats_y + 38), label, fill=TEXT_LIGHT, font=FONT_SMALL)

    # Table
    table_y = 220
    draw.rectangle([(content_x, table_y), (content_x + content_width, height - 30)], fill=CARD_BG, outline=BORDER)

    # Table header
    draw.rectangle([(content_x, table_y), (content_x + content_width, table_y + 40)], fill="#F8FAFC")
    headers = ["Numero", "Client", "Date", "Montant", "Statut"]
    col_widths = [120, 200, 100, 120, 100]
    hx = content_x + 15
    for header, w in zip(headers, col_widths):
        draw.text((hx, table_y + 12), header, fill=TEXT_LIGHT, font=FONT_SMALL)
        hx += w

    # Table rows
    invoices = [
        ("FAC-2024-156", "Tech Solutions SARL", "15/02/2024", "2 450 EUR", "Payee", SUCCESS),
        ("FAC-2024-155", "Dupont Industries", "14/02/2024", "1 890 EUR", "Envoyee", WARNING),
        ("FAC-2024-154", "Martin & Fils", "12/02/2024", "3 200 EUR", "Payee", SUCCESS),
        ("FAC-2024-153", "Garage Central", "10/02/2024", "890 EUR", "En retard", DANGER),
        ("FAC-2024-152", "Boulangerie Paul", "08/02/2024", "450 EUR", "Payee", SUCCESS),
        ("FAC-2024-151", "Cabinet Durand", "05/02/2024", "1 200 EUR", "Payee", SUCCESS),
    ]

    row_y = table_y + 50
    for num, client, date, amount, status, color in invoices:
        rx = content_x + 15
        draw.text((rx, row_y), num, fill=TEXT_DARK, font=FONT_SMALL); rx += 120
        draw.text((rx, row_y), client[:18], fill=TEXT_DARK, font=FONT_SMALL); rx += 200
        draw.text((rx, row_y), date, fill=TEXT_LIGHT, font=FONT_SMALL); rx += 100
        draw.text((rx, row_y), amount, fill=TEXT_DARK, font=FONT_BOLD); rx += 120
        draw.rectangle([(rx, row_y - 2), (rx + 70, row_y + 18)], fill=color)
        draw.text((rx + 8, row_y), status, fill="#FFFFFF", font=FONT_SMALL)
        row_y += 45
        draw.line([(content_x + 10, row_y - 15), (content_x + content_width - 10, row_y - 15)], fill=BORDER)

    img.save(OUTPUT_DIR / "mockup-commercial.png", quality=95)
    print("Created: mockup-commercial.png")


def create_crm_mockup():
    """Slide 3: CRM - Contacts"""
    width, height = 1200, 750
    img = Image.new('RGB', (width, height), DARK_BG)
    draw = ImageDraw.Draw(img)

    sidebar_width = draw_sidebar(draw, width, height, "CRM")
    content_x = sidebar_width + 30
    content_width = width - sidebar_width - 60

    # Header
    draw.text((content_x, 30), "CRM - Contacts", fill="#FFFFFF", font=FONT_LARGE)

    # Search bar
    search_y = 75
    draw.rectangle([(content_x, search_y), (content_x + 300, search_y + 36)], fill="#2D3748", outline="#4A5568")
    draw.text((content_x + 15, search_y + 10), "Rechercher un contact...", fill="#64748B", font=FONT_SMALL)

    # Add button
    draw.rectangle([(content_x + 320, search_y), (content_x + 450, search_y + 36)], fill=PRIMARY)
    draw.text((content_x + 335, search_y + 10), "+ Nouveau contact", fill="#FFFFFF", font=FONT_SMALL)

    # Stats
    stats_y = 130
    crm_stats = [("156", "Contacts"), ("42", "Prospects"), ("89", "Clients"), ("25", "Fournisseurs")]
    stat_w = 140
    for i, (val, label) in enumerate(crm_stats):
        x = content_x + i * (stat_w + 15)
        draw.rectangle([(x, stats_y), (x + stat_w, stats_y + 65)], fill=CARD_BG, outline=BORDER)
        draw.text((x + 15, stats_y + 10), val, fill=PRIMARY, font=FONT_LARGE)
        draw.text((x + 15, stats_y + 42), label, fill=TEXT_LIGHT, font=FONT_SMALL)

    # Contact cards grid
    card_y = 215
    card_w = 285
    card_h = 160

    contacts = [
        ("Marie Dupont", "Tech Solutions SARL", "Directrice", "marie@techsol.fr", "06 12 34 56 78", "Client"),
        ("Jean Martin", "Martin & Fils", "Gerant", "j.martin@mf.fr", "06 98 76 54 32", "Client"),
        ("Sophie Bernard", "Garage Central", "Comptable", "s.bernard@gc.fr", "06 11 22 33 44", "Prospect"),
        ("Pierre Durand", "Cabinet Durand", "Avocat", "p.durand@cab.fr", "06 55 66 77 88", "Client"),
        ("Anne Leroy", "Boulangerie Paul", "Gerante", "a.leroy@bp.fr", "06 99 88 77 66", "Client"),
        ("Marc Thomas", "Import Export SA", "Commercial", "m.thomas@ie.fr", "06 44 33 22 11", "Prospect"),
    ]

    for i, (name, company, role, email, phone, ctype) in enumerate(contacts):
        row = i // 3
        col = i % 3
        x = content_x + col * (card_w + 15)
        y = card_y + row * (card_h + 15)

        draw.rectangle([(x, y), (x + card_w, y + card_h)], fill=CARD_BG, outline=BORDER)

        # Avatar circle
        draw.ellipse([(x + 15, y + 15), (x + 55, y + 55)], fill=PRIMARY)
        draw.text((x + 28, y + 25), name[0], fill="#FFFFFF", font=FONT_BOLD)

        # Info
        draw.text((x + 70, y + 15), name, fill=TEXT_DARK, font=FONT_BOLD)
        draw.text((x + 70, y + 35), company[:22], fill=TEXT_LIGHT, font=FONT_SMALL)
        draw.text((x + 15, y + 70), role, fill=TEXT_LIGHT, font=FONT_SMALL)
        draw.text((x + 15, y + 90), email, fill=PRIMARY, font=FONT_SMALL)
        draw.text((x + 15, y + 110), phone, fill=TEXT_LIGHT, font=FONT_SMALL)

        # Type badge
        badge_color = SUCCESS if ctype == "Client" else WARNING
        draw.rectangle([(x + card_w - 70, y + 15), (x + card_w - 10, y + 33)], fill=badge_color)
        draw.text((x + card_w - 62, y + 18), ctype, fill="#FFFFFF", font=FONT_SMALL)

    img.save(OUTPUT_DIR / "mockup-crm.png", quality=95)
    print("Created: mockup-crm.png")


def create_inventory_mockup():
    """Slide 4: Inventaire"""
    width, height = 1200, 750
    img = Image.new('RGB', (width, height), DARK_BG)
    draw = ImageDraw.Draw(img)

    sidebar_width = draw_sidebar(draw, width, height, "Inventaire")
    content_x = sidebar_width + 30
    content_width = width - sidebar_width - 60

    # Header
    draw.text((content_x, 30), "Gestion des stocks", fill="#FFFFFF", font=FONT_LARGE)

    # Action buttons
    btn_y = 75
    draw.rectangle([(content_x, btn_y), (content_x + 130, btn_y + 36)], fill=PRIMARY)
    draw.text((content_x + 15, btn_y + 10), "+ Nouveau produit", fill="#FFFFFF", font=FONT_SMALL)

    # Stats
    stats_y = 130
    inv_stats = [
        ("1 245", "Produits", PRIMARY),
        ("12", "Stock faible", WARNING),
        ("3", "Rupture", DANGER),
        ("156 400 EUR", "Valeur stock", SUCCESS),
    ]
    stat_w = 160
    for i, (val, label, color) in enumerate(inv_stats):
        x = content_x + i * (stat_w + 15)
        draw.rectangle([(x, stats_y), (x + stat_w, stats_y + 70)], fill=CARD_BG, outline=BORDER)
        draw.text((x + 15, stats_y + 12), val, fill=color, font=FONT_BOLD)
        draw.text((x + 15, stats_y + 38), label, fill=TEXT_LIGHT, font=FONT_SMALL)

    # Products table
    table_y = 220
    draw.rectangle([(content_x, table_y), (content_x + content_width, height - 30)], fill=CARD_BG, outline=BORDER)

    # Table header
    draw.rectangle([(content_x, table_y), (content_x + content_width, table_y + 40)], fill="#F8FAFC")
    headers = ["Reference", "Designation", "Stock", "Seuil", "Prix", "Statut"]
    col_widths = [100, 220, 80, 80, 100, 100]
    hx = content_x + 15
    for header, w in zip(headers, col_widths):
        draw.text((hx, table_y + 12), header, fill=TEXT_LIGHT, font=FONT_SMALL)
        hx += w

    # Products
    products = [
        ("PRD-001", "Ecran LED 27 pouces", "45", "10", "299 EUR", "OK", SUCCESS),
        ("PRD-002", "Clavier mecanique RGB", "8", "15", "89 EUR", "Faible", WARNING),
        ("PRD-003", "Souris sans fil", "0", "20", "49 EUR", "Rupture", DANGER),
        ("PRD-004", "Cable HDMI 2m", "234", "50", "12 EUR", "OK", SUCCESS),
        ("PRD-005", "Hub USB-C 7 ports", "67", "20", "45 EUR", "OK", SUCCESS),
        ("PRD-006", "Casque audio BT", "5", "10", "129 EUR", "Faible", WARNING),
        ("PRD-007", "Webcam HD 1080p", "89", "15", "79 EUR", "OK", SUCCESS),
    ]

    row_y = table_y + 50
    for ref, name, stock, seuil, price, status, color in products:
        rx = content_x + 15
        draw.text((rx, row_y), ref, fill=TEXT_DARK, font=FONT_SMALL); rx += 100
        draw.text((rx, row_y), name[:20], fill=TEXT_DARK, font=FONT_SMALL); rx += 220
        draw.text((rx, row_y), stock, fill=TEXT_DARK, font=FONT_BOLD); rx += 80
        draw.text((rx, row_y), seuil, fill=TEXT_LIGHT, font=FONT_SMALL); rx += 80
        draw.text((rx, row_y), price, fill=TEXT_DARK, font=FONT_SMALL); rx += 100
        draw.rectangle([(rx, row_y - 2), (rx + 65, row_y + 18)], fill=color)
        draw.text((rx + 10, row_y), status, fill="#FFFFFF", font=FONT_SMALL)
        row_y += 42
        draw.line([(content_x + 10, row_y - 12), (content_x + content_width - 10, row_y - 12)], fill=BORDER)

    img.save(OUTPUT_DIR / "mockup-inventory.png", quality=95)
    print("Created: mockup-inventory.png")


def create_security_mockup():
    """Slide 5: Securite et conformite"""
    width, height = 1200, 750
    img = Image.new('RGB', (width, height), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Full dark background for security theme
    draw.rectangle([(0, 0), (width, height)], fill=DARK_BG)

    # Center content
    center_x = width // 2

    # Title
    draw.text((center_x - 200, 60), "Securite & Conformite", fill="#FFFFFF", font=FONT_XLARGE)
    draw.text((center_x - 180, 110), "Vos donnees sont entre de bonnes mains", fill="#94A3B8", font=FONT_MEDIUM)

    # Security badges in a grid
    badges = [
        ("RGPD", "Conforme au reglement europeen", SUCCESS),
        ("AES-256", "Chiffrement de niveau bancaire", PRIMARY),
        ("France", "Donnees hebergees en France", PRIMARY),
        ("99.9%", "Disponibilite garantie SLA", SUCCESS),
        ("2FA", "Authentification renforcee", PRIMARY),
        ("Backup", "Sauvegardes quotidiennes", SUCCESS),
    ]

    badge_w = 320
    badge_h = 100
    start_x = (width - (badge_w * 3 + 40)) // 2
    start_y = 180

    for i, (title, desc, color) in enumerate(badges):
        row = i // 3
        col = i % 3
        x = start_x + col * (badge_w + 20)
        y = start_y + row * (badge_h + 20)

        draw.rectangle([(x, y), (x + badge_w, y + badge_h)], fill=SIDEBAR_BG, outline=color)

        # Icon circle
        draw.ellipse([(x + 15, y + 25), (x + 55, y + 65)], fill=color)
        draw.text((x + 27, y + 35), title[0], fill="#FFFFFF", font=FONT_BOLD)

        # Text
        draw.text((x + 70, y + 25), title, fill="#FFFFFF", font=FONT_BOLD)
        draw.text((x + 70, y + 50), desc, fill="#94A3B8", font=FONT_SMALL)

    # E-Facture 2026 banner
    banner_y = 420
    draw.rectangle([(start_x, banner_y), (width - start_x, banner_y + 80)], fill=PRIMARY)
    draw.text((center_x - 120, banner_y + 15), "Pret pour e-Facture 2026", fill="#FFFFFF", font=FONT_LARGE)
    draw.text((center_x - 180, banner_y + 50), "Conformite automatique avec la reforme de facturation electronique", fill="#E0E7FF", font=FONT_SMALL)

    # Certifications row
    cert_y = 540
    draw.text((center_x - 80, cert_y), "Certifications", fill="#FFFFFF", font=FONT_BOLD)

    certs = ["ISO 27001", "SOC 2", "ANSSI", "HDS"]
    cert_x = center_x - 200
    for cert in certs:
        draw.rectangle([(cert_x, cert_y + 40), (cert_x + 90, cert_y + 75)], fill=SIDEBAR_BG, outline="#4A5568")
        draw.text((cert_x + 15, cert_y + 50), cert, fill="#94A3B8", font=FONT_SMALL)
        cert_x += 105

    # Trust indicators
    trust_y = 650
    draw.text((center_x - 280, trust_y), "Plus de 500 entreprises nous font confiance", fill="#64748B", font=FONT_MEDIUM)

    img.save(OUTPUT_DIR / "mockup-security.png", quality=95)
    print("Created: mockup-security.png")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generation des mockups...")
    create_dashboard_mockup()
    create_commercial_mockup()
    create_crm_mockup()
    create_inventory_mockup()
    create_security_mockup()

    print("\nTermine ! Images generees:")
    for f in sorted(OUTPUT_DIR.glob("mockup-*.png")):
        print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
