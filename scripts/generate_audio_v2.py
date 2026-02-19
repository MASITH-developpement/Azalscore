#!/usr/bin/env python3
"""
AZALSCORE - Generate Audio with Microsoft Edge TTS
Voix française naturelle - texte simple sans SSML
"""

import asyncio
import edge_tts
from pathlib import Path

OUTPUT_DIR = Path("/home/ubuntu/azalscore/frontend/public/audio")

# Voix française naturelle
VOICE = "fr-FR-DeniseNeural"

# Scripts en texte simple - la ponctuation crée les pauses naturelles
SLIDES = [
    {
        "name": "slide1",
        "text": "Bienvenue sur Azalscore ! Votre tableau de bord intelligent vous donne une vue complète de votre activité. Chiffre d'affaires, factures en attente, nouveaux clients... Tout est visible en un coup d'œil !"
    },
    {
        "name": "slide2",
        "text": "La gestion commerciale n'a jamais été aussi simple ! Créez vos devis et factures en quelques clics. Suivez les paiements et les relances automatiquement. Fini les impayés oubliés !"
    },
    {
        "name": "slide3",
        "text": "Le CRM intégré centralise tous vos contacts. Prospects, clients, fournisseurs... Chaque interaction est enregistrée. Vous ne perdez plus jamais une opportunité !"
    },
    {
        "name": "slide4",
        "text": "Gérez votre inventaire en temps réel ! Alertes automatiques en cas de stock faible. Valorisation instantanée. Vous gardez toujours le contrôle !"
    },
    {
        "name": "slide5",
        "text": "Azalscore, c'est aussi la sécurité ! Conforme RGPD, chiffrement bancaire, données hébergées en France. Et vous êtes déjà prêt pour la e-facture 2026 ! Essayez gratuitement pendant 30 jours."
    },
]


async def generate_audio_file(text: str, output_path: Path, voice: str):
    """Génère un fichier audio avec Edge TTS"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Génération des fichiers audio avec voix {VOICE}...")

    for slide in SLIDES:
        output_path = OUTPUT_DIR / f"{slide['name']}.mp3"
        await generate_audio_file(slide['text'], output_path, VOICE)
        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ {slide['name']}.mp3 ({size_kb:.1f} KB)")

    print(f"\n✅ Terminé !")


if __name__ == "__main__":
    asyncio.run(main())
