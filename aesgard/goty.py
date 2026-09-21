# -*- coding: utf-8 -*-
"""
GOTY (Game of the Year) module for Choose Random Game.
Curates an official historical database of GOTY winners from 1983 to 2025
(The Game Awards, Spike VGA, BAFTA, D.I.C.E. Awards, Golden Joystick, GDC).
Cross-references GOTY titles with the user's installed library.
"""
import random
import logging
import sqlite3
import jellyfish
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Complete historical catalog of Game of the Year winners (1983 - 2024/2025)
GOTY_CATALOG = [
    # 2020s
    {
        "year": 2024,
        "title": "Astro Bot",
        "developer": "Team Asobi / Sony Interactive Entertainment",
        "genre": "Plataforma 3D",
        "platform": "PlayStation 5",
        "awards": "The Game Awards (GOTY), Golden Joystick (GOTY)",
        "summary": "Uma celebração vibrante e criativa da história dos videogames com jogabilidade de plataforma primorosa."
    },
    {
        "year": 2024,
        "title": "Black Myth: Wukong",
        "developer": "Game Science",
        "genre": "Ação / RPG",
        "platform": "PC / PS5",
        "awards": "Golden Joystick (Ultimate Game of the Year)",
        "summary": "Ação intensa e mitologia chinesa inspirada na clássica lenda de Jornada ao Oeste."
    },
    {
        "year": 2023,
        "title": "Baldur's Gate 3",
        "developer": "Larian Studios",
        "genre": "CRPG",
        "platform": "PC / PS5 / Xbox Series",
        "awards": "The Game Awards (GOTY), BAFTA, D.I.C.E., GDC, Golden Joystick",
        "summary": "Obra-prima do RPG com liberdade sem precedentes, narrativa profunda baseada em Dungeons & Dragons."
    },
    {
        "year": 2023,
        "title": "The Legend of Zelda: Tears of the Kingdom",
        "developer": "Nintendo EPD",
        "genre": "Ação / Aventura",
        "platform": "Nintendo Switch",
        "awards": "The Game Awards (Melhor Ação/Aventura), Famitsu GOTY",
        "summary": "Expansão revolucionária de Hyrule com sistemas inovadores de construção e exploração vertical."
    },
    {
        "year": 2022,
        "title": "Elden Ring",
        "developer": "FromSoftware",
        "genre": "Action RPG / Souls-like",
        "platform": "PC / PlayStation / Xbox",
        "awards": "The Game Awards (GOTY), D.I.C.E., GDC, Golden Joystick, Japan Game Awards",
        "summary": "Marco nos jogos de mundo aberto com combate visceral e colaboração criativa com George R. R. Martin."
    },
    {
        "year": 2022,
        "title": "God of War Ragnarök",
        "developer": "Santa Monica Studio",
        "genre": "Ação / Aventura",
        "platform": "PlayStation / PC",
        "awards": "BAFTA (EE Game of the Year), Titanium Awards",
        "summary": "A conclusão épica da jornada nórdica de Kratos e Atreus contra o panteão de Asgard."
    },
    {
        "year": 2021,
        "title": "It Takes Two",
        "developer": "Hazelight Studios / EA Originals",
        "genre": "Plataforma Cooperativa / Aventura",
        "platform": "PC / PlayStation / Xbox / Switch",
        "awards": "The Game Awards (GOTY), D.I.C.E., GDC (GOTY)",
        "summary": "Aventura exclusivamente cooperativa engenhosa que mistura dezenas de gêneros em prol da narrativa."
    },
    {
        "year": 2021,
        "title": "Resident Evil Village",
        "developer": "Capcom",
        "genre": "Survival Horror / Ação",
        "platform": "PC / PlayStation / Xbox",
        "awards": "Golden Joystick (Ultimate Game of the Year)",
        "summary": "A saga de Ethan Winters contra os lordes de um vilarejo gótico europeu misterioso."
    },
    {
        "year": 2020,
        "title": "The Last of Us Part II",
        "developer": "Naughty Dog",
        "genre": "Ação / Aventura / Stealth",
        "platform": "PlayStation",
        "awards": "The Game Awards (GOTY), Golden Joystick, D.I.C.E., BAFTA",
        "summary": "Narrativa cinematográfica impiedosa e visceral sobre vingança, obsessão e empatia."
    },
    {
        "year": 2020,
        "title": "Hades",
        "developer": "Supergiant Games",
        "genre": "Roguelike / Action RPG",
        "platform": "PC / PlayStation / Xbox / Switch",
        "awards": "BAFTA (GOTY), D.I.C.E., GDC, Hugo Awards",
        "summary": "Roguelike frenético e envolvente ambientado no submundo da mitologia grega com trilha sonora espetacular."
    },

    # 2010s
    {
        "year": 2019,
        "title": "Sekiro: Shadows Die Twice",
        "developer": "FromSoftware",
        "genre": "Ação / Aventura",
        "platform": "PC / PlayStation / Xbox",
        "awards": "The Game Awards (GOTY), Steam Awards",
        "summary": "Combate rítmico implacável focado em deflexões de espadas no Japão do período Sengoku."
    },
    {
        "year": 2019,
        "title": "Untitled Goose Game",
        "developer": "House House",
        "genre": "Stealth / Quebra-cabeça",
        "platform": "PC / Consoles",
        "awards": "D.I.C.E. (GOTY), GDC (GOTY)",
        "summary": "Um ganso travesso causando caos hilário em um pacato vilarejo britânico."
    },
    {
        "year": 2018,
        "title": "God of War",
        "developer": "Santa Monica Studio",
        "genre": "Ação / Aventura",
        "platform": "PlayStation / PC",
        "awards": "The Game Awards (GOTY), BAFTA, D.I.C.E., GDC",
        "summary": "Reivenção magistral da franquia com câmera em plano-sequência e emocionante relação pai e filho."
    },
    {
        "year": 2018,
        "title": "Red Dead Redemption 2",
        "developer": "Rockstar Games",
        "genre": "Mundo Aberto / Faroeste",
        "platform": "PC / PlayStation / Xbox",
        "awards": "Golden Joystick (Critics Choice), The Game Awards (4 categorias)",
        "summary": "O mais detalhado e imersivo simulador de faroeste da história, narrando a queda da gangue Van der Linde."
    },
    {
        "year": 2017,
        "title": "The Legend of Zelda: Breath of the Wild",
        "developer": "Nintendo EPD",
        "genre": "Ação / Aventura / Mundo Aberto",
        "platform": "Nintendo Switch / Wii U",
        "awards": "The Game Awards (GOTY), D.I.C.E., GDC, Golden Joystick, Japan Game Awards",
        "summary": "Redefiniu a liberdade nos videogames com exploração química e física orgânica em Hyrule."
    },
    {
        "year": 2016,
        "title": "Overwatch",
        "developer": "Blizzard Entertainment",
        "genre": "Hero Shooter",
        "platform": "PC / Consoles",
        "awards": "The Game Awards (GOTY), D.I.C.E., GDC",
        "summary": "Hero shooter vibrante que conquistou o mundo com elenco carismático e partidas táticas dinâmicas."
    },
    {
        "year": 2016,
        "title": "Uncharted 4: A Thief's End",
        "developer": "Naughty Dog",
        "genre": "Ação / Aventura",
        "platform": "PlayStation / PC",
        "awards": "BAFTA (GOTY), Titanium Awards",
        "summary": "A despedida comovente de Nathan Drake em busca do lendário tesouro pirata de Libertalia."
    },
    {
        "year": 2015,
        "title": "The Witcher 3: Wild Hunt",
        "developer": "CD Projekt Red",
        "genre": "Action RPG",
        "platform": "PC / PlayStation / Xbox / Switch",
        "awards": "The Game Awards (GOTY), Golden Joystick, GDC",
        "summary": "Um dos RPGs mais aclamados de todos os tempos, guiando Geralt de Rivia em busca de Ciri."
    },
    {
        "year": 2015,
        "title": "Bloodborne",
        "developer": "FromSoftware",
        "genre": "Action RPG / Horror Cósmico",
        "platform": "PlayStation 4",
        "awards": "Golden Joystick (PlayStation GOTY), EDGE GOTY",
        "summary": "Atmosfera vitoriana e gótica com caçadores velozes enfrentando horrores cósmicos em Yharnam."
    },
    {
        "year": 2014,
        "title": "Dragon Age: Inquisition",
        "developer": "BioWare",
        "genre": "RPG",
        "platform": "PC / PlayStation / Xbox",
        "awards": "The Game Awards (Primeiro GOTY oficial do TGA), D.I.C.E.",
        "summary": "Lidere a Inquisição para fechar a fenda nos céus e restaurar a ordem no continente de Thedas."
    },
    {
        "year": 2013,
        "title": "Grand Theft Auto V",
        "developer": "Rockstar North",
        "genre": "Ação / Mundo Aberto",
        "platform": "PC / PlayStation / Xbox",
        "awards": "Spike VGX (GOTY), Golden Joystick",
        "summary": "Fenômeno cultural unindo Michael, Franklin e Trevor em assaltos épicos em Los Santos."
    },
    {
        "year": 2013,
        "title": "The Last of Us",
        "developer": "Naughty Dog",
        "genre": "Ação / Aventura / Survival",
        "platform": "PlayStation / PC",
        "awards": "BAFTA (GOTY), D.I.C.E., GDC, Annie Awards",
        "summary": "Jornada pós-apocalíptica inesquecível de Joel e Ellie pelos Estados Unidos devastados pelo Cordyceps."
    },
    {
        "year": 2012,
        "title": "The Walking Dead",
        "developer": "Telltale Games",
        "genre": "Aventura Gráfica / Narrativa",
        "platform": "Multiplataforma",
        "awards": "Spike VGA (GOTY), BAFTA, USA Today GOTY",
        "summary": "Pioneiro da narrativa interativa com escolhas morais pesadas entre Lee Everett e a jovem Clementine."
    },
    {
        "year": 2012,
        "title": "Journey",
        "developer": "thatgamecompany",
        "genre": "Aventura Artística",
        "platform": "PlayStation / PC",
        "awards": "D.I.C.E. (GOTY), GDC (GOTY)",
        "summary": "Experiência poética e transcendental através de desertos dourados e templos esquecidos."
    },
    {
        "year": 2011,
        "title": "The Elder Scrolls V: Skyrim",
        "developer": "Bethesda Game Studios",
        "genre": "Action RPG / Mundo Aberto",
        "platform": "PC / PlayStation / Xbox / Switch",
        "awards": "Spike VGA (GOTY), D.I.C.E., GDC",
        "summary": "O lendário RPG onde você assume o papel de Dragonborn em meio a dragões e guerras civis em Skyrim."
    },
    {
        "year": 2011,
        "title": "Portal 2",
        "developer": "Valve",
        "genre": "Quebra-cabeça / Primeira Pessoa",
        "platform": "PC / PlayStation / Xbox / Switch",
        "awards": "BAFTA (GOTY), Golden Joystick",
        "summary": "Roteiro brilhante, humor afiado com GLaDOS e Wheatley e mecânicas de física espacial lendárias."
    },
    {
        "year": 2010,
        "title": "Red Dead Redemption",
        "developer": "Rockstar San Diego",
        "genre": "Ação / Faroeste",
        "platform": "PlayStation / Xbox / Switch / PC",
        "awards": "Spike VGA (GOTY), GDC",
        "summary": "A clássica redenção de John Marston pela fronteira do velho oeste americano e México."
    },
    {
        "year": 2010,
        "title": "Mass Effect 2",
        "developer": "BioWare",
        "genre": "RPG / Sci-Fi",
        "platform": "PC / PlayStation / Xbox",
        "awards": "D.I.C.E. (GOTY), BAFTA (GOTY), Golden Joystick",
        "summary": "O comandante Shepard reunindo uma equipe de elite para uma missão suicida além do relé Ômega 4."
    },

    # 2000s
    {
        "year": 2009,
        "title": "Uncharted 2: Among Thieves",
        "developer": "Naughty Dog",
        "genre": "Ação / Aventura",
        "platform": "PlayStation",
        "awards": "Spike VGA (GOTY), D.I.C.E., GDC",
        "summary": "Ritmo espetacular de cinema com Nathan Drake em busca da lendária pedra Cintamani e Shambhala."
    },
    {
        "year": 2008,
        "title": "Fallout 3",
        "developer": "Bethesda Game Studios",
        "genre": "Action RPG / Pós-Apocalíptico",
        "platform": "PC / PlayStation / Xbox",
        "awards": "GDC (GOTY), Golden Joystick",
        "summary": "Explore os ermos devastados da capital Washington D.C. após o holocausto nuclear."
    },
    {
        "year": 2007,
        "title": "BioShock",
        "developer": "Irrational Games",
        "genre": "FPS / Immersive Sim",
        "platform": "PC / PlayStation / Xbox",
        "awards": "Spike VGA (GOTY), BAFTA (GOTY)",
        "summary": "A deslumbrante e aterrorizante cidade subaquática distópica de Rapture criada por Andrew Ryan."
    },
    {
        "year": 2006,
        "title": "The Elder Scrolls IV: Oblivion",
        "developer": "Bethesda Game Studios",
        "genre": "Action RPG",
        "platform": "PC / PlayStation / Xbox",
        "awards": "Spike VGA (GOTY), Golden Joystick",
        "summary": "Feche os portões de Oblivion para salvar a província de Cyrodiil da invasão de Mehrunes Dagon."
    },
    {
        "year": 2005,
        "title": "Resident Evil 4",
        "developer": "Capcom",
        "genre": "Survival Horror / Ação",
        "platform": "GameCube / PS2 / PC / Multi",
        "awards": "Spike VGA (GOTY), Nintendo Power GOTY",
        "summary": "Revolucionou os jogos em terceira pessoa com câmera sobre o ombro e ação tensa na Espanha rural."
    },
    {
        "year": 2004,
        "title": "Half-Life 2",
        "developer": "Valve",
        "genre": "FPS / Sci-Fi",
        "platform": "PC / Xbox",
        "awards": "Spike VGA (GOTY), BAFTA, GDC, D.I.C.E.",
        "summary": "Gordon Freeman e a Gravity Gun liderando a resistência humana contra a invasão Combine na City 17."
    },
    {
        "year": 2004,
        "title": "Grand Theft Auto: San Andreas",
        "developer": "Rockstar North",
        "genre": "Mundo Aberto / Ação",
        "platform": "PS2 / PC / Xbox",
        "awards": "Golden Joystick (Ultimate Game of the Year)",
        "summary": "CJ retornando a Los Santos dos anos 90 em um mundo gigantesco repleto de liberdade e gangues."
    },
    {
        "year": 2003,
        "title": "Star Wars: Knights of the Old Republic",
        "developer": "BioWare",
        "genre": "RPG",
        "platform": "PC / Xbox",
        "awards": "GDC (GOTY), D.I.C.E. (GOTY)",
        "summary": "Uma das maiores tramas de Star Wars já escritas, ambientada 4.000 anos antes do Império Galáctico."
    },
    {
        "year": 2002,
        "title": "Grand Theft Auto: Vice City",
        "developer": "Rockstar North",
        "genre": "Mundo Aberto / Ação",
        "platform": "PS2 / PC / Xbox",
        "awards": "Golden Joystick (GOTY), BAFTA",
        "summary": "Estética dos anos 80, neon, palmeiras e Tommy Vercetti dominando o submundo do crime de Vice City."
    },
    {
        "year": 2001,
        "title": "Halo: Combat Evolved",
        "developer": "Bungie",
        "genre": "FPS / Sci-Fi",
        "platform": "Xbox / PC",
        "awards": "D.I.C.E. (GOTY), BAFTA",
        "summary": "Consagrou os jogos de tiro em consoles com Master Chief combatendo o Covenant no anel misterioso de Halo."
    },
    {
        "year": 2001,
        "title": "Grand Theft Auto III",
        "developer": "DMA Design / Rockstar Games",
        "genre": "Mundo Aberto / Ação 3D",
        "platform": "PS2 / PC / Xbox",
        "awards": "GDC (Game of the Year)",
        "summary": "O marco histórico que transmutou os jogos de mundo aberto para o universo 3D com Liberty City."
    },
    {
        "year": 2000,
        "title": "Deus Ex",
        "developer": "Ion Storm",
        "genre": "Immersive Sim / RPG / Cyberpunk",
        "platform": "PC",
        "awards": "BAFTA, PC Gamer GOTY",
        "summary": "Clássico seminal de ficção científica cyberpunk com conspirações globais e liberdade tática ilimitada."
    },

    # 1990s
    {
        "year": 1999,
        "title": "System Shock 2",
        "developer": "Irrational Games / Looking Glass",
        "genre": "Sci-Fi Horror / Immersive Sim",
        "platform": "PC",
        "awards": "IGN GOTY, PC Gamer GOTY",
        "summary": "A IA vilã mais aterrorizante da história, SHODAN, a bordo da espaçonave Von Braun."
    },
    {
        "year": 1998,
        "title": "The Legend of Zelda: Ocarina of Time",
        "developer": "Nintendo EAD",
        "genre": "Ação / Aventura",
        "platform": "Nintendo 64",
        "awards": "D.I.C.E. (Inaugural GOTY 1999), Japan Media Arts",
        "summary": "Com frequência considerado o melhor jogo de todos os tempos, introduzindo a mira Z-targeting e viagem no tempo."
    },
    {
        "year": 1998,
        "title": "Half-Life",
        "developer": "Valve",
        "genre": "FPS / Sci-Fi",
        "platform": "PC",
        "awards": "Over 50 Game of the Year Awards",
        "summary": "Revolucionou a narrativa dos shooters com o desastre de Black Mesa vivido em tempo real por Gordon Freeman."
    },
    {
        "year": 1997,
        "title": "Final Fantasy VII",
        "developer": "Square",
        "genre": "JRPG",
        "platform": "PlayStation / PC",
        "awards": "Golden Joystick (GOTY), Origins Award",
        "summary": "Popularizou os JRPGs no ocidente com Cloud Strife combatendo a megacorporação Shinra e Sephiroth."
    },
    {
        "year": 1996,
        "title": "Super Mario 64",
        "developer": "Nintendo EAD",
        "genre": "Plataforma 3D",
        "platform": "Nintendo 64",
        "awards": "Golden Joystick, Spotlight Awards",
        "summary": "A pedra fundamental de todos os jogos 3D da história, ensinando como mover a câmera e personagens no espaço tridimensional."
    },
    {
        "year": 1995,
        "title": "Chrono Trigger",
        "developer": "Square",
        "genre": "JRPG",
        "platform": "Super Nintendo / PC",
        "awards": "Electronic Gaming Monthly GOTY",
        "summary": "Obra-prima com 'Dream Team' (Sakaguchi, Horii e Toriyama) sobre viagem através das eras do tempo."
    },
    {
        "year": 1994,
        "title": "Doom II: Hell on Earth",
        "developer": "id Software",
        "genre": "FPS",
        "platform": "PC / DOS",
        "awards": "Origins Award GOTY",
        "summary": "Super shotgun, hordas demoníacas e o ápice do design de níveis dos shooters em DOS."
    },
    {
        "year": 1993,
        "title": "Doom",
        "developer": "id Software",
        "genre": "FPS",
        "platform": "PC / DOS",
        "awards": "PC Gamer GOTY",
        "summary": "O jogo que definiu o gênero de tiro em primeira pessoa e mudou a cultura dos games para sempre."
    },
    {
        "year": 1992,
        "title": "Street Fighter II",
        "developer": "Capcom",
        "genre": "Luta",
        "platform": "Arcade / SNES",
        "awards": "Golden Joystick (GOTY), Electronic Gaming Monthly",
        "summary": "O pai de todos os jogos de luta competitivos modernos e um fenômeno absoluto das casas de fliperama."
    },
    {
        "year": 1991,
        "title": "The Legend of Zelda: A Link to the Past",
        "developer": "Nintendo EAD",
        "genre": "Ação / Aventura",
        "platform": "Super Nintendo",
        "awards": "Famitsu (Melhor Jogo), EGM GOTY",
        "summary": "A aventura definitiva em 16-bits transitando entre os mundos da Luz e das Trevas de Hyrule."
    },
    {
        "year": 1990,
        "title": "Super Mario World",
        "developer": "Nintendo EAD",
        "genre": "Plataforma",
        "platform": "Super Nintendo",
        "awards": "Nintendo Power GOTY",
        "summary": "A introdução de Yoshi e um mapa com dezenas de segredos na consagrada Dinosaur Land."
    },

    # 1980s
    {
        "year": 1989,
        "title": "Tetris",
        "developer": "Alexey Pajitnov / Nintendo",
        "genre": "Quebra-cabeça",
        "platform": "Game Boy / Arcade / PC",
        "awards": "Golden Joystick (GOTY), Origins Award",
        "summary": "O jogo de puzzle mais famoso, viciante e influente de todos os tempos."
    },
    {
        "year": 1988,
        "title": "Super Mario Bros. 3",
        "developer": "Nintendo R&D4",
        "genre": "Plataforma",
        "platform": "NES",
        "awards": "Electronic Gaming Monthly GOTY",
        "summary": "Mundo expansivo com mapa de fases, power-up de Tanooki e design de níveis lendário."
    },
    {
        "year": 1987,
        "title": "The Legend of Zelda",
        "developer": "Nintendo R&D4",
        "genre": "Ação / Aventura",
        "platform": "NES",
        "awards": "Famitsu (Clássico Ouro), Game Player's GOTY",
        "summary": "Pioneiro absoluto da exploração não-linear com o cartucho dourado icônico e bateria de salvamento."
    },
    {
        "year": 1986,
        "title": "Out Run",
        "developer": "Sega AM2 (Yu Suzuki)",
        "genre": "Corrida / Arcade",
        "platform": "Arcade",
        "awards": "Golden Joystick (Game of the Year)",
        "summary": "Ferrari Testarossa, trilha sonora de rádio inovadora e bifurcações de rota no clássico da Sega."
    },
    {
        "year": 1985,
        "title": "Super Mario Bros.",
        "developer": "Nintendo R&D4",
        "genre": "Plataforma",
        "platform": "NES",
        "awards": "Golden Joystick, Hall da Fama dos Games",
        "summary": "O marco histórico que redefiniu o mercado de consoles e consagrou Shigeru Miyamoto."
    },
    {
        "year": 1984,
        "title": "Elite",
        "developer": "David Braben & Ian Bell",
        "genre": "Simulação Espacial / Comércio",
        "platform": "BBC Micro / PC",
        "awards": "Golden Joystick (Melhor Jogo Britânico)",
        "summary": "Pioneiro da geração procedural de galáxias e gráficos 3D wireframe no espaço."
    },
    {
        "year": 1983,
        "title": "Dragon's Lair",
        "developer": "Cinematronics / Don Bluth",
        "genre": "Interactive Movie / Aventura",
        "platform": "Arcade / Laserdisc",
        "awards": "Arkie Awards (Coin-op of the Year)",
        "summary": "Revolução visual histórica trazendo animação cinematográfica de Don Bluth para os fliperamas."
    }
]

import re
import os

def extractTitleNumber(text: str) -> str:
    """Extracts trailing or isolated numbers / roman numerals (e.g. 2, 3, iv, v, vi)."""
    tokens = re.findall(r'\b([0-9]+|[ivx]+)\b', text.lower())
    valid = [t for t in tokens if t in ('i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x') or t.isdigit()]
    return valid[-1] if valid else ""

def cleanTitleForMatch(text: str) -> str:
    """Normalizes game title for robust matching without destructive character stripping."""
    if not text:
        return ""
    clean = text.lower()
    clean = re.sub(r'\b(the|edition|definitive|remastered|game of the year|goty|cut|directors|enhanced)\b', '', clean)
    clean = re.sub(r'[^a-z0-9]', '', clean)
    return clean.strip()

def extractEntryGameTitle(entry: str) -> str:
    """Extracts human-readable game title from any library entry string."""
    if entry.startswith("playnite:"):
        parts = entry.split(":")
        if len(parts) >= 3:
            return parts[2]
        elif len(parts) >= 2:
            return parts[1]
        return entry
    elif entry.startswith("link::"):
        clean_path = entry[len("link::"):]
        base = os.path.basename(clean_path)
        title, _ = os.path.splitext(base)
        return title
    elif entry.startswith("exodos:"):
        path = entry[len("exodos:"):]
        return os.path.basename(path.rstrip('/\\'))
    else:
        clean = entry.replace("\\", "/").rstrip("/")
        folder_title = clean.split("/")[-1]
        return folder_title

def isGotyInstalledInLibrary(gotyTitle: str, userGamesList: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Checks if a GOTY game matches any entry currently in the user's library with high fidelity.
    Returns (is_installed: bool, matched_library_entry: str or None).
    """
    clean_goty = cleanTitleForMatch(gotyTitle)
    goty_num = extractTitleNumber(gotyTitle)
    if not clean_goty or len(clean_goty) < 3:
        return (False, None)

    for entry in userGamesList:
        entry_title = extractEntryGameTitle(entry)
        clean_entry = cleanTitleForMatch(entry_title)
        entry_num = extractTitleNumber(entry_title)
        
        if not clean_entry or len(clean_entry) < 3:
            continue

        # If numbers / roman numerals differ, they are different games in a franchise!
        if goty_num != entry_num:
            if goty_num or entry_num:
                continue

        # 1. Exact match
        if clean_goty == clean_entry:
            return (True, entry)

        # 2. Strong containment: GOTY title is inside entry title (e.g. "Baldur's Gate 3" in "Baldur's Gate 3 Deluxe")
        if len(clean_goty) >= 4 and clean_goty in clean_entry:
            return (True, entry)

        # 3. Reverse containment: only if entry covers >= 85% of GOTY
        if len(clean_entry) >= 6 and clean_entry in clean_goty and (len(clean_entry) / len(clean_goty) >= 0.85):
            return (True, entry)

        # 4. High similarity (Jaro-Winkler) - only if comparable length
        len_ratio = min(len(clean_goty), len(clean_entry)) / max(len(clean_goty), len(clean_entry))
        if len(clean_goty) >= 6 and len(clean_entry) >= 6 and len_ratio >= 0.85:
            sim = jellyfish.jaro_winkler_similarity(clean_goty, clean_entry)
            if sim >= 0.94:
                return (True, entry)

    return (False, None)

def initGotyDatabase(conn: sqlite3.Connection, userGamesList: Optional[List[str]] = None):
    """
    Initializes the GotyGames table in the database and seeds it with historical winners.
    Updates the is_installed flag based on the user's active library using fast pre-parsing.
    """
    user_games = userGamesList or []
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS GotyGames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                title TEXT UNIQUE,
                developer TEXT,
                genre TEXT,
                platform TEXT,
                awards TEXT,
                summary TEXT,
                is_installed INTEGER DEFAULT 0,
                library_entry TEXT
            );
        """)

        # Fast in-memory parsing of active user games
        parsed_library = []
        for entry in user_games:
            title = extractEntryGameTitle(entry)
            clean = cleanTitleForMatch(title)
            num = extractTitleNumber(title)
            if clean and len(clean) >= 3:
                parsed_library.append((entry, title, clean, num))

        # Insert or update each catalog item
        for item in GOTY_CATALOG:
            clean_goty = cleanTitleForMatch(item["title"])
            goty_num = extractTitleNumber(item["title"])
            found_entry = None

            for entry, entry_title, clean_entry, entry_num in parsed_library:
                if goty_num != entry_num:
                    if goty_num or entry_num:
                        continue
                if clean_goty == clean_entry:
                    found_entry = entry
                    break
                if len(clean_goty) >= 4 and clean_goty in clean_entry:
                    found_entry = entry
                    break
                if len(clean_entry) >= 6 and clean_entry in clean_goty and (len(clean_entry) / len(clean_goty) >= 0.85):
                    found_entry = entry
                    break
                len_ratio = min(len(clean_goty), len(clean_entry)) / max(len(clean_goty), len(clean_entry))
                if len(clean_goty) >= 6 and len(clean_entry) >= 6 and len_ratio >= 0.85:
                    sim = jellyfish.jaro_winkler_similarity(clean_goty, clean_entry)
                    if sim >= 0.94:
                        found_entry = entry
                        break

            is_inst = found_entry is not None
            cursor.execute("""
                INSERT INTO GotyGames (year, title, developer, genre, platform, awards, summary, is_installed, library_entry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title) DO UPDATE SET
                    year = excluded.year,
                    developer = excluded.developer,
                    genre = excluded.genre,
                    platform = excluded.platform,
                    awards = excluded.awards,
                    summary = excluded.summary,
                    is_installed = excluded.is_installed,
                    library_entry = excluded.library_entry;
            """, (
                item["year"],
                item["title"],
                item["developer"],
                item["genre"],
                item["platform"],
                item["awards"],
                item["summary"],
                1 if is_inst else 0,
                found_entry or ""
            ))
        conn.commit()
        logger.info(f"GotyGames table synced with {len(GOTY_CATALOG)} historical titles.")
    except Exception as e:
        logger.warning(f"Error seeding GotyGames database: {e}")
    finally:
        cursor.close()


def getRandomGoty(conn: sqlite3.Connection) -> Optional[Dict]:
    """Retrieves a random Game of the Year from the database."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, year, title, developer, genre, platform, awards, summary, is_installed, library_entry FROM GotyGames")
        rows = cursor.fetchall()
        if not rows:
            return None
        chosen = random.choice(rows)
        return {
            "id": chosen[0],
            "year": chosen[1],
            "title": chosen[2],
            "developer": chosen[3],
            "genre": chosen[4],
            "platform": chosen[5],
            "awards": chosen[6],
            "summary": chosen[7],
            "is_installed": bool(chosen[8]),
            "library_entry": chosen[9]
        }
    except Exception as e:
        logger.warning(f"Error querying random GOTY: {e}")
        return None
    finally:
        cursor.close()

def getAllGotys(conn: sqlite3.Connection) -> List[Dict]:
    """Retrieves all GOTY games sorted descending by year."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, year, title, developer, genre, platform, awards, summary, is_installed, library_entry FROM GotyGames ORDER BY year DESC, title ASC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "year": r[1],
                "title": r[2],
                "developer": r[3],
                "genre": r[4],
                "platform": r[5],
                "awards": r[6],
                "summary": r[7],
                "is_installed": bool(r[8]),
                "library_entry": r[9]
            })
        return result
    except Exception as e:
        logger.warning(f"Error querying all GOTYs: {e}")
        return []
    finally:
        cursor.close()
