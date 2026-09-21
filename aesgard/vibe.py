# -*- coding: utf-8 -*-
"""
Vibe / Mood Picker & Curator Pitch Engine for Choose Random Game.
Categorizes games into emotional vibes (Zen, Adrenaline, Horror, Story, Retro, Strategy)
and synthesizes engaging micro-reviews/pitches for the streamer.
"""
import re
from typing import Dict, List, Optional
from aesgard.ui import formatDisplayName, detectPlatform
from aesgard.hltb import get_cached_hltb, clean_title_for_hltb, format_hltb_duration

# The 6 Curated Vibes
VIBES = {
    "zen": {
        "key": "zen",
        "name": "Zen & Relaxar",
        "emoji": "🧘",
        "color": "#10b981", # Emerald
        "desc": "Jogos tranquilos, acolhedores, quebra-cabeças e exploração sem estresse.",
        "keywords": {
            "puzzle", "relax", "cozy", "walk", "sim", "farm", "garden", "golf",
            "island", "kart", "party", "flight", "tetris", "bubble", "pinball",
            "chess", "card", "board", "monument", "journey", "abzu", "stray",
            "slime", "craft", "coffee", "dorfromantik", "unpacking", "hike", "donut"
        }
    },
    "adrenaline": {
        "key": "adrenaline",
        "name": "Pura Adrenalina",
        "emoji": "⚡",
        "color": "#f59e0b", # Amber
        "desc": "Ação frenética, tiro em primeira pessoa, velocidade e combate visceral.",
        "keywords": {
            "doom", "quake", "unreal", "call of duty", "battlefield", "halo",
            "speed", "race", "racing", "burnout", "need for speed", "forza",
            "nfs", "dirt", "f1", "rally", "tony hawk", "skate", "tekken",
            "mortal kombat", "street fighter", "smash", "devil may cry", "bayonetta",
            "ninja", "bullet", "contra", "metal slug", "kill", "warrior", "sniper",
            "wolfenstein", "titanfall", "payday", "overwatch", "action", "arena", "rush"
        }
    },
    "horror": {
        "key": "horror",
        "name": "Terror & Suspense",
        "emoji": "👻",
        "color": "#8b5cf6", # Purple
        "desc": "Survival horror, sustos ao vivo, atmosfera opressiva e mistério sombrio.",
        "keywords": {
            "resident evil", "silent hill", "outlast", "amnesia", "fnaf", "dead space",
            "evil", "fear", "dark", "blood", "nightmare", "blair witch", "haunt",
            "demon", "zombie", "alien: isolation", "soma", "slender", "hunt",
            "phantasmagoria", "clive barker", "undying", "alone in the dark", "penumbra",
            "horror", "terror", "creepy", "parasite eve", "condemned", "fatal frame"
        }
    },
    "story": {
        "key": "story",
        "name": "História & Imersão",
        "emoji": "📜",
        "color": "#06b6d4", # Cyan
        "desc": "Narrativas ricas, universos profundos, RPGs memoráveis e diálogos marcantes.",
        "keywords": {
            "witcher", "skyrim", "fallout", "baldur", "dragon age", "mass effect",
            "final fantasy", "persona", "chrono", "yakuza", "cyberpunk", "red dead",
            "gta", "grand theft auto", "kingdom come", "deus ex", "bioshock", "dishonored",
            "alan wake", "life is strange", "walking dead", "detroit", "heavy rain",
            "quest", "chronicles", "tales", "valkyria", "divinity", "rpg", "lore"
        }
    },
    "retro": {
        "key": "retro",
        "name": "Nostalgia Retrô & Arcade",
        "emoji": "🕹️",
        "color": "#ec4899", # Pink
        "desc": "Clássicos imortais de arcade, MS-DOS e consoles de 8/16-bit.",
        "keywords": {
            "mario", "sonic", "castlevania", "mega man", "metroid", "zelda", "dk",
            "donkey kong", "pac-man", "galaga", "space invaders", "golden axe",
            "streets of rage", "sunset riders", "final fight", "cadillacs", "tmnt",
            "contra", "arcade", "exodos", "dosbox", "commodore", "atari", "nes",
            "snes", "genesis", "master system", "amiga"
        }
    },
    "strategy": {
        "key": "strategy",
        "name": "Estratégia & Raciocínio",
        "emoji": "🧠",
        "color": "#3b82f6", # Blue
        "desc": "Táticas por turnos, estratégia em tempo real, gestão e grandes decisões.",
        "keywords": {
            "civilization", "crusader", "age of empires", "starcraft", "warcraft",
            "command & conquer", "heroes of might and magic", "total war", "xcom",
            "tactics", "ogre", "stellaris", "europa", "simcity", "tycoon", "rollercoaster",
            "factorio", "rimworld", "anno", "settlers", "strategy", "turn-based", "rts"
        }
    }
}


def classify_game_vibe(game_entry: str) -> Dict:
    """
    Classifies a game entry into one of the 6 vibes based on title and platform heuristics.
    Returns the vibe dictionary.
    """
    clean = clean_title_for_hltb(formatDisplayName(game_entry)).lower()
    platform = detectPlatform(game_entry)

    # 1. Platform checks for Retro
    if platform in ("eXoDOS", "DOSBox", "NES", "SNES", "Arcade", "MAME", "Master System", "Mega Drive", "Game Boy", "Atari"):
        # If explicitly horror in retro, allow horror, else default retro
        if any(kw in clean for kw in VIBES["horror"]["keywords"]):
            return VIBES["horror"]
        return VIBES["retro"]

    # 2. Check keywords across vibes
    scores = {k: 0 for k in VIBES}
    for k, v in VIBES.items():
        for kw in v["keywords"]:
            if kw in clean:
                scores[k] += len(kw)  # longer keyword match = higher confidence

    best_vibe_key = max(scores, key=scores.get)
    if scores[best_vibe_key] > 0:
        return VIBES[best_vibe_key]

    # Default fallback heuristics
    if "rpg" in clean or "quest" in clean:
        return VIBES["story"]
    elif "2" in clean or "3" in clean or "combat" in clean:
        return VIBES["adrenaline"]
    else:
        return VIBES["zen"]


def filter_games_by_vibe(content: List[str], vibe_key: str) -> List[str]:
    """Filters library games matching the given vibe key."""
    if vibe_key not in VIBES:
        return content
    target_vibe = VIBES[vibe_key]
    kws = target_vibe["keywords"]

    matches = []
    for g in content:
        c = clean_title_for_hltb(formatDisplayName(g)).lower()
        # Direct retro platform check
        if vibe_key == "retro":
            plat = detectPlatform(g)
            if plat in ("eXoDOS", "DOSBox", "NES", "SNES", "Arcade", "MAME", "Master System", "Mega Drive", "Game Boy", "Atari"):
                matches.append(g)
                continue
        if any(kw in c for kw in kws):
            matches.append(g)

    # Fallback to random slice if too strict
    if len(matches) < 3:
        return [g for g in content if classify_game_vibe(g)["key"] == vibe_key] or content
    return matches


def generate_curator_pitch(game_entry: str, hltb_info: Optional[Dict] = None) -> Dict:
    """
    Generates an engaging, high-energy curator pitch ("Por que jogar hoje?")
    for the streamer and their community.
    """
    title = formatDisplayName(game_entry)
    platform = detectPlatform(game_entry)
    vibe = classify_game_vibe(game_entry)
    
    if not hltb_info:
        hltb_info = get_cached_hltb(title) or {}

    hours = hltb_info.get("main_story", 0.0) if hltb_info else 0.0
    dur_str = f"~{format_hltb_duration(hours)}" if hours > 0 else "Tempo livre / flexível"

    hooks = {
        "zen": [
            "Perfeito para relaxar a cabeça e bater papo gostoso com o chat!",
            "Jogabilidade suave e envolvente que não exige reflexos sobre-humanos.",
            "Visual aconchegante que transmite uma paz imediata para a live."
        ],
        "adrenaline": [
            "Ritmo alucinante do primeiro ao último minuto!",
            "Excelente para testar os reflexos e ver o chat torcendo a cada esquina.",
            "Combate afiado com alta energia na tela!"
        ],
        "horror": [
            "Garante os melhores sustos e clipes hilários para a transmissão!",
            "Atmosfera tensa de roer as unhas que prende a audiência do início ao fim.",
            "Apague as luzes, coloque os fones e prepare o coração!"
        ],
        "story": [
            "Uma jornada cinematográfica com personagens e diálogos inesquecíveis.",
            "Perfeito para quem quer se perder em um universo rico e tomar decisões de peso.",
            "História instigante que faz o chat virar co-piloto da aventura."
        ],
        "retro": [
            "Pura nostalgia e aula de game design dos tempos de ouro dos videogames!",
            "Desafio raiz da era dos fliperamas: precisão cirúrgica e trilha sonora marcante.",
            "Aquela sensação deliciosa de soprar o cartucho e reviver memórias!"
        ],
        "strategy": [
            "Onde cada decisão conta e o plano brilhante (ou o desastre) fica na sua mão!",
            "Estimula o chat a opinar nas táticas e criar reviravoltas mirabolantes.",
            "Profundidade tática que recompensa quem pensa dois passos à frente."
        ]
    }

    import hashlib
    # Deterministic selection based on title hash so pitch remains consistent for the game
    idx = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    hook = hooks.get(vibe["key"], hooks["zen"])[idx % 3]

    streamer_tips = {
        "zen": "💡 Dica de Live: Coloque uma música lo-fi de fundo e convide o chat para desabafar sobre o dia!",
        "adrenaline": "💡 Dica de Live: Peça para o chat avisar quando piscar, porque o ritmo não vai parar!",
        "horror": "💡 Dica de Live: Crie uma meta de sustos ou configure os pontos do canal para jumpscares!",
        "story": "💡 Dica de Live: Faça votações rápidas antes de decisões morais ou diálogos ramificados!",
        "retro": "💡 Dica de Live: Conte uma curiosidade de infância sobre a época em que esse jogo foi lançado!",
        "strategy": "💡 Dica de Live: Nomeie suas tropas ou personagens com os nicks dos inscritos do chat!"
    }

    return {
        "title": title,
        "platform": platform,
        "vibe_name": vibe["name"],
        "vibe_emoji": vibe["emoji"],
        "vibe_color": vibe["color"],
        "vibe_desc": vibe["desc"],
        "hook": hook,
        "duration": dur_str,
        "streamer_tip": streamer_tips.get(vibe["key"], "")
    }
