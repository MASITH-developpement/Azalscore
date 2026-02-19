#!/usr/bin/env python3
"""
AZALSCORE - Generate Expressive Audio with Microsoft Edge TTS
Voix française naturelle avec intonation et expression
"""

import asyncio
import edge_tts
from pathlib import Path

OUTPUT_DIR = Path("/home/ubuntu/azalscore/frontend/public/audio")

# Voix française expressive (Denise = voix féminine naturelle et dynamique)
VOICE = "fr-FR-DeniseNeural"

# Scripts avec annotations SSML pour l'expression
SLIDES = [
    {
        "name": "slide1",
        "text": """
        <speak>
            <prosody rate="medium" pitch="+5%">
                Bienvenue sur Azalscore !
            </prosody>
            <break time="300ms"/>
            Votre tableau de bord intelligent vous donne une vue <emphasis level="moderate">complète</emphasis> de votre activité.
            <break time="200ms"/>
            Chiffre d'affaires, factures en attente, nouveaux clients...
            <break time="300ms"/>
            <prosody rate="slow" pitch="+3%">
                Tout est visible en un coup d'œil.
            </prosody>
        </speak>
        """
    },
    {
        "name": "slide2",
        "text": """
        <speak>
            <prosody rate="medium">
                La gestion commerciale n'a <emphasis level="strong">jamais</emphasis> été aussi simple !
            </prosody>
            <break time="300ms"/>
            Créez vos devis et factures en quelques clics.
            <break time="200ms"/>
            Suivez les paiements et les relances <emphasis level="moderate">automatiquement</emphasis>.
            <break time="300ms"/>
            <prosody pitch="+5%">
                Fini les impayés oubliés !
            </prosody>
        </speak>
        """
    },
    {
        "name": "slide3",
        "text": """
        <speak>
            <prosody rate="medium">
                Le CRM intégré centralise <emphasis level="moderate">tous</emphasis> vos contacts.
            </prosody>
            <break time="300ms"/>
            Prospects, clients, fournisseurs...
            <break time="200ms"/>
            Chaque interaction est enregistrée.
            <break time="400ms"/>
            <prosody rate="slow" pitch="+3%">
                Vous ne perdez plus jamais une opportunité.
            </prosody>
        </speak>
        """
    },
    {
        "name": "slide4",
        "text": """
        <speak>
            Gérez votre inventaire en <emphasis level="strong">temps réel</emphasis>.
            <break time="300ms"/>
            <prosody rate="medium">
                Alertes automatiques en cas de stock faible.
                <break time="200ms"/>
                Valorisation instantanée.
            </prosody>
            <break time="400ms"/>
            <prosody pitch="+5%">
                Vous gardez toujours le contrôle !
            </prosody>
        </speak>
        """
    },
    {
        "name": "slide5",
        "text": """
        <speak>
            <prosody rate="medium">
                Azalscore, c'est aussi la <emphasis level="strong">sécurité</emphasis>.
            </prosody>
            <break time="300ms"/>
            Conforme RGPD, chiffrement bancaire, données hébergées en France.
            <break time="400ms"/>
            <prosody rate="slow" pitch="+5%">
                Et vous êtes déjà prêt pour la e-facture 2026 !
            </prosody>
            <break time="300ms"/>
            <prosody rate="medium" pitch="+8%">
                Essayez gratuitement pendant 30 jours.
            </prosody>
        </speak>
        """
    },
]


async def generate_audio_file(text: str, output_path: Path, voice: str):
    """Génère un fichier audio avec Edge TTS"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Génération des fichiers audio avec voix {VOICE}...")
    print("(Voix française expressive avec intonation)\n")

    for slide in SLIDES:
        output_path = OUTPUT_DIR / f"{slide['name']}.mp3"

        # Nettoyer le texte SSML
        text = slide['text'].strip()

        await generate_audio_file(text, output_path, VOICE)

        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ {slide['name']}.mp3 ({size_kb:.1f} KB)")

    print(f"\n✅ Terminé ! Fichiers dans {OUTPUT_DIR}")
    print("\nVoix utilisée: Microsoft Denise (fr-FR-DeniseNeural)")
    print("Caractéristiques: Naturelle, expressive, dynamique")


if __name__ == "__main__":
    asyncio.run(main())
