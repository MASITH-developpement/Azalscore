#!/usr/bin/env python3
"""
AZALSCORE - Generate Audio for Demo Slides
Uses Google Text-to-Speech to create French voice-over
"""

from gtts import gTTS
from pathlib import Path

OUTPUT_DIR = Path("/home/ubuntu/azalscore/frontend/public/audio")

# Script pour chaque slide
SLIDES = [
    {
        "name": "slide1",
        "text": "Bienvenue sur Azalscore. Votre tableau de bord intelligent vous donne une vue complète de votre activité. Chiffre d'affaires, factures en attente, nouveaux clients. Tout est visible en un coup d'œil."
    },
    {
        "name": "slide2",
        "text": "La gestion commerciale n'a jamais été aussi simple. Créez vos devis et factures en quelques clics. Suivez les paiements et les relances automatiquement. Fini les impayés oubliés."
    },
    {
        "name": "slide3",
        "text": "Le CRM intégré centralise tous vos contacts. Prospects, clients, fournisseurs. Chaque interaction est enregistrée. Vous ne perdez plus jamais une opportunité."
    },
    {
        "name": "slide4",
        "text": "Gérez votre inventaire en temps réel. Alertes automatiques en cas de stock faible. Valorisation instantanée. Vous gardez toujours le contrôle."
    },
    {
        "name": "slide5",
        "text": "Azalscore, c'est aussi la sécurité. Conforme RGPD, chiffrement bancaire, données hébergées en France. Et vous êtes déjà prêt pour la e-facture 2026."
    },
]

def generate_audio():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Génération des fichiers audio...")

    for slide in SLIDES:
        output_path = OUTPUT_DIR / f"{slide['name']}.mp3"

        tts = gTTS(text=slide['text'], lang='fr', slow=False)
        tts.save(str(output_path))

        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ {slide['name']}.mp3 ({size_kb:.1f} KB)")

    print(f"\nTerminé ! Fichiers dans {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_audio()
