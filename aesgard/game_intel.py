# -*- coding: utf-8 -*-
"""
Game Intelligence & Walkthrough Module for Choose Random Game.
Collects rich data for live streaming:
- Synopsis and storyline (Wikipedia REST API, Steam, GOG)
- Direct links for Walkthroughs & Guides (GameFAQs, IGN, PCGamingWiki, YouTube)
- HowLongToBeat campaign estimates
- Local manual and doc finder for retro/eXoDOS games
"""
import os
import re
import logging
import requests
from typing import Dict, List, Optional
from aesgard.covers import getCleanGameTitle
from aesgard.ui import formatDisplayName

logger = logging.getLogger(__name__)

def getGuideLinks(gameTitle: str) -> Dict[str, str]:
    """Generates direct 1-click guide and walkthrough search URLs for streaming."""
    clean = re.sub(r'\(.*?\)', '', gameTitle)
    clean = re.sub(r'\[.*?\]', '', clean).replace('.lnk', '').replace('.exe', '').strip()
    encoded = requests.utils.quote(clean)

    return {
        "GameFAQs": f"https://gamefaqs.gamespot.com/search?game={encoded}",
        "IGN Guides": f"https://www.ign.com/search?q={encoded}+guide",
        "PCGamingWiki": f"https://www.pcgamingwiki.com/w/index.php?search={encoded}",
        "HowLongToBeat": f"https://howlongtobeat.com/?q={encoded}",
        "YouTube Walkthrough": f"https://www.youtube.com/results?search_query={encoded}+full+gameplay+walkthrough",
        "Speedrun.com": f"https://www.speedrun.com/search?term={encoded}",
        "Google Dicas": f"https://www.google.com/search?q={encoded}+dicas+detonado+guia"
    }

def findLocalGameManuals(gameEntry: str) -> List[Dict[str, str]]:
    """
    Finds manuals, maps, hint sheets and documentation inside eXoDOS or local game folders.
    """
    manuals = []
    target_dirs = []

    if gameEntry.startswith("exodos:"):
        path = gameEntry[7:]
        target_dirs.extend([
            path,
            os.path.join(path, "Docs"),
            os.path.join(path, "Extras")
        ])
    elif not gameEntry.startswith("playnite:") and not gameEntry.startswith("link::"):
        # Local folder
        if os.path.isdir(gameEntry):
            target_dirs.extend([
                gameEntry,
                os.path.join(gameEntry, "Docs"),
                os.path.join(gameEntry, "Manuals"),
                os.path.join(gameEntry, "Extras")
            ])

    allowed_exts = ('.pdf', '.txt', '.doc', '.docx', '.html', '.htm')
    for d in target_dirs:
        if os.path.isdir(d):
            try:
                for f in os.listdir(d):
                    if f.lower().endswith(allowed_exts):
                        full_p = os.path.join(d, f)
                        manuals.append({
                            "name": f,
                            "path": full_p,
                            "ext": os.path.splitext(f)[1].lower()
                        })
            except Exception:
                pass

    return manuals

def fetchGameSynopsis(gameTitle: str, timeout: int = 4) -> Dict[str, str]:
    """
    Fetches game synopsis, description and developer details from Wikipedia REST API.
    """
    clean = getCleanGameTitle(gameTitle)
    result = {
        "title": clean,
        "summary": "Sinopse não disponível automaticamente. Use os links de guias para consultar informações detalhadas.",
        "developer": "",
        "genre": "",
        "releaseDate": "",
        "source": ""
    }

    # Try Wikipedia REST API
    queries = [f"{clean} (video game)", clean]
    headers = {'User-Agent': 'ChooseRandomGame/2.0 (Gaming Live Stream Assistant)'}

    for q in queries:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(q)}"
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract")
                if extract and len(extract) > 40:
                    result["summary"] = extract
                    result["source"] = "Wikipedia"
                    desc = data.get("description", "")
                    if desc:
                        result["genre"] = desc
                    return result
        except Exception:
            continue

    return result

def getFullGameIntel(gameEntry: str) -> Dict:
    """Aggregates all intelligence data for a given game."""
    display_title = formatDisplayName(gameEntry)
    clean_title = getCleanGameTitle(gameEntry)

    synopsis_data = fetchGameSynopsis(clean_title)
    guide_links = getGuideLinks(clean_title)
    manuals = findLocalGameManuals(gameEntry)

    return {
        "rawEntry": gameEntry,
        "displayTitle": display_title,
        "cleanTitle": clean_title,
        "summary": synopsis_data.get("summary", ""),
        "genre": synopsis_data.get("genre", ""),
        "source": synopsis_data.get("source", ""),
        "guideLinks": guide_links,
        "manuals": manuals
    }
