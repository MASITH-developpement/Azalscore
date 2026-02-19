#!/usr/bin/env python3
"""
AZALSCORE - Generate Short Audio for Social Media Video (< 1 min total)
Environ 10 secondes par slide = 50 secondes total
"""

import asyncio
import edge_tts
from pathlib import Path

OUTPUT_DIR = Path("/home/ubuntu/azalscore/frontend/public/audio")
VOICE = "fr-FR-DeniseNeural"

# Textes courts pour moins d'1 minute total
SLIDES = [
    {
        "name": "slide1",
        "text": "Azalscore, l'ERP français pour les PME. Votre tableau de bord centralise toute votre activité en temps réel."
    },
    {
        "name": "slide2",
        "text": "Factures et devis en quelques clics. Suivi des paiements automatique. Fini les impayés oubliés !"
    },
    {
        "name": "slide3",
        "text": "CRM intégré : tous vos contacts, prospects et clients centralisés. Ne perdez plus aucune opportunité."
    },
    {
        "name": "slide4",
        "text": "Gestion des stocks en temps réel. Alertes automatiques. Vous gardez le contrôle."
    },
    {
        "name": "slide5",
        "text": "100% français, conforme RGPD, prêt pour 2026. Essayez gratuitement 30 jours sur azalscore.com !"
    },
]

async def generate_audio_file(text: str, output_path: Path, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Génération des audios courts (< 1 min total)...")

    total_size = 0
    for slide in SLIDES:
        output_path = OUTPUT_DIR / f"{slide['name']}.mp3"
        await generate_audio_file(slide['text'], output_path, VOICE)
        size_kb = output_path.stat().st_size / 1024
        total_size += size_kb
        print(f"  ✓ {slide['name']}.mp3 ({size_kb:.1f} KB)")

    print(f"\nTotal: {total_size:.1f} KB")
    print("Durée estimée: ~50 secondes")

if __name__ == "__main__":
    asyncio.run(main())
