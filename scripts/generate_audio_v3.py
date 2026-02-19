#!/usr/bin/env python3
"""
AZALSCORE - Generate Audio for Real Interface Demo
"""

import asyncio
import edge_tts
from pathlib import Path

OUTPUT_DIR = Path("/home/ubuntu/azalscore/frontend/public/audio")
VOICE = "fr-FR-DeniseNeural"

SLIDES = [
    {
        "name": "slide1",
        "text": "Bienvenue sur Azalscore ! Créez un devis en quelques secondes. Sélectionnez votre client, ajoutez vos produits ou services, et c'est prêt !"
    },
    {
        "name": "slide2",
        "text": "L'interface est simple et intuitive. Pas besoin de formation ! Tout est pensé pour vous guider étape par étape."
    },
    {
        "name": "slide3",
        "text": "La recherche client est intelligente. Trouvez vos clients instantanément, ou créez-en de nouveaux directement depuis le formulaire."
    },
    {
        "name": "slide4",
        "text": "Ajoutez vos produits et services en toute flexibilité. Quantités, prix unitaires... Le calcul des totaux est automatique !"
    },
    {
        "name": "slide5",
        "text": "Azalscore est 100% français et sécurisé. Conforme RGPD, prêt pour la e-facture 2026. Vos données sont hébergées en France. Essayez gratuitement pendant 30 jours !"
    },
]

async def generate_audio_file(text: str, output_path: Path, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Génération des audios avec voix {VOICE}...")

    for slide in SLIDES:
        output_path = OUTPUT_DIR / f"{slide['name']}.mp3"
        await generate_audio_file(slide['text'], output_path, VOICE)
        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ {slide['name']}.mp3 ({size_kb:.1f} KB)")

    print("Terminé !")

if __name__ == "__main__":
    asyncio.run(main())
