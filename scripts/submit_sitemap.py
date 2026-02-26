#!/usr/bin/env python3
"""
AZALSCORE - Script de soumission du sitemap aux moteurs de recherche

Ce script soumet le sitemap.xml aux principaux moteurs de recherche :
- Google (via ping)
- Bing (via ping + IndexNow)
- Yandex (via ping)

Usage:
    python scripts/submit_sitemap.py

Requiert: httpx (pip install httpx)
"""

import asyncio
import logging
from datetime import datetime

# Configuration
SITEMAP_URL = "https://azalscore.com/sitemap.xml"
SITE_URL = "https://azalscore.com"
INDEXNOW_KEY = "azalscore-indexnow-2026-key"

# URLs de soumission des moteurs de recherche
SEARCH_ENGINES = {
    "Google": f"https://www.google.com/ping?sitemap={SITEMAP_URL}",
    "Bing": f"https://www.bing.com/ping?sitemap={SITEMAP_URL}",
    "Yandex": f"https://webmaster.yandex.com/ping?sitemap={SITEMAP_URL}",
}

# URLs IndexNow
INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]

# Pages a notifier via IndexNow
PAGES_TO_INDEX = [
    "/",
    "/features",
    "/pricing",
    "/demo",
    "/contact",
    "/about",
    "/docs",
    "/essai-gratuit",
    "/mentions-legales",
    "/confidentialite",
    "/cgv",
    "/login",
]

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def ping_search_engine(name: str, url: str) -> dict:
    """Ping un moteur de recherche pour soumettre le sitemap."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                logger.info(f"[OK] {name}: Sitemap soumis avec succes")
                return {"engine": name, "success": True, "status": response.status_code}
            else:
                logger.warning(f"[WARN] {name}: Status {response.status_code}")
                return {"engine": name, "success": False, "status": response.status_code}

    except Exception as e:
        logger.error(f"[ERROR] {name}: {e}")
        return {"engine": name, "success": False, "error": str(e)}


async def submit_indexnow(pages: list) -> dict:
    """Soumet les URLs via IndexNow a Bing, Yandex, etc."""
    import httpx

    results = {"success": [], "failed": []}
    full_urls = [f"{SITE_URL}{page}" for page in pages]

    payload = {
        "host": "azalscore.com",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": full_urls
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in INDEXNOW_ENDPOINTS:
            try:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code in [200, 202]:
                    logger.info(f"[OK] IndexNow ({endpoint}): {len(full_urls)} URLs soumises")
                    results["success"].append(endpoint)
                else:
                    logger.warning(f"[WARN] IndexNow ({endpoint}): Status {response.status_code}")
                    results["failed"].append({
                        "endpoint": endpoint,
                        "status": response.status_code
                    })

            except Exception as e:
                logger.error(f"[ERROR] IndexNow ({endpoint}): {e}")
                results["failed"].append({
                    "endpoint": endpoint,
                    "error": str(e)
                })

    return results


async def main():
    """Point d'entree principal."""
    logger.info("=" * 60)
    logger.info("AZALSCORE - Soumission Sitemap aux Moteurs de Recherche")
    logger.info(f"Date: {datetime.now().isoformat()}")
    logger.info(f"Sitemap: {SITEMAP_URL}")
    logger.info("=" * 60)

    # 1. Ping des moteurs de recherche
    logger.info("\n[ETAPE 1] Ping des moteurs de recherche...")
    ping_tasks = [
        ping_search_engine(name, url)
        for name, url in SEARCH_ENGINES.items()
    ]
    ping_results = await asyncio.gather(*ping_tasks)

    # 2. Soumission IndexNow
    logger.info("\n[ETAPE 2] Soumission IndexNow...")
    indexnow_results = await submit_indexnow(PAGES_TO_INDEX)

    # Resume
    logger.info("\n" + "=" * 60)
    logger.info("RESUME")
    logger.info("=" * 60)

    successful_pings = sum(1 for r in ping_results if r.get("success"))
    logger.info(f"Ping moteurs: {successful_pings}/{len(SEARCH_ENGINES)} reussis")
    logger.info(f"IndexNow: {len(indexnow_results['success'])}/{len(INDEXNOW_ENDPOINTS)} reussis")
    logger.info(f"URLs soumises: {len(PAGES_TO_INDEX)}")

    # Instructions supplementaires
    logger.info("\n" + "=" * 60)
    logger.info("PROCHAINES ETAPES MANUELLES")
    logger.info("=" * 60)
    logger.info("""
1. Google Search Console:
   - Aller sur https://search.google.com/search-console
   - Ajouter la propriete azalscore.com
   - Soumettre le sitemap manuellement

2. Bing Webmaster Tools:
   - Aller sur https://www.bing.com/webmasters
   - Ajouter le site azalscore.com
   - Verifier la propriete avec le fichier HTML ou meta tag
   - Soumettre le sitemap

3. Yandex Webmaster:
   - Aller sur https://webmaster.yandex.com
   - Ajouter le site azalscore.com
   - Soumettre le sitemap

4. Google Business Profile (si applicable):
   - Creer un profil Google Business
   - Lier au site web

5. Reseaux sociaux:
   - Partager les pages cles sur LinkedIn, Twitter
   - Les meta OG sont configurees pour un bon rendu
""")

    return {
        "ping_results": ping_results,
        "indexnow_results": indexnow_results,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    asyncio.run(main())
