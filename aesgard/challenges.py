# -*- coding: utf-8 -*-
"""
Streamer Challenge & Live Modifier Engine for Choose Random Game.
Provides randomized live challenges, handicaps, and chat penalties
with real-time OBS Web Overlay synchronization.
"""
import random
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

CHALLENGES: List[Dict] = [
    # --- Sobrevivência Selvagem (Jack London / Caninos Brancos) ---
    {
        "id": "white_fang_instinct",
        "category": "Selva do Yukon 🐺",
        "title": "A Lei da Selva (Instinto Puro)",
        "desc": "Jogue no instinto: proibido pausar para pensar ou consultar guias/mapas nesta caçada!",
        "icon": "🐺",
        "color": "#38bdf8"
    },
    {
        "id": "lone_wolf",
        "category": "Selva do Yukon 🐺",
        "title": "Lobo Solitário",
        "desc": "Proibido recrutar companheiros, invocar summons ou pedir dicas ao chat nos primeiros 30 min!",
        "icon": "❄️",
        "color": "#0ea5e9"
    },
    {
        "id": "blizzard_endurance",
        "category": "Selva do Yukon 🐺",
        "title": "Resistência à Nevasca",
        "desc": "Sobreviva 1 hora de gameplay contínua sem nenhum Game Over na trilha congelada!",
        "icon": "🏔️",
        "color": "#10b981"
    },

    # --- Hardcore ---
    {
        "id": "no_heal",
        "category": "Hardcore 💀",
        "title": "Sem Cura Permitida",
        "desc": "Proibido usar poções ou itens de recuperação de vida durante a primeira hora.",
        "icon": "💊",
        "color": "#ef4444"
    },
    {
        "id": "no_damage_boss",
        "category": "Hardcore 💀",
        "title": "Boss Impecável (No-Hit)",
        "desc": "O primeiro chefe ou grande encontro deve ser vencido sem tomar nenhum golpe!",
        "icon": "🛡️",
        "color": "#ef4444"
    },
    {
        "id": "starter_gear",
        "category": "Hardcore 💀",
        "title": "Armamento Raiz",
        "desc": "Jogue apenas com a arma inicial ou kit básico pelo máximo de tempo possível.",
        "icon": "🗡️",
        "color": "#ef4444"
    },
    {
        "id": "no_hud",
        "category": "Hardcore 💀",
        "title": "Modo Cinema Imersivo",
        "desc": "Desative o minimapa e o HUD nas configurações do jogo para navegação pura.",
        "icon": "👁️",
        "color": "#ef4444"
    },

    # --- Cômico & Penalidades ---
    {
        "id": "pushups",
        "category": "Cômico & Castigo 😂",
        "title": "Morte = 10 Flexões",
        "desc": "A cada morte ou 'Game Over', pague 10 flexões, polichinelos ou agachamentos ao vivo!",
        "icon": "💪",
        "color": "#f59e0b"
    },
    {
        "id": "voice_acting",
        "category": "Cômico & Castigo 😂",
        "title": "Dublagem Dramática",
        "desc": "Duble e encene todas as falas e grunhidos dos personagens com voz teatral!",
        "icon": "🎙️",
        "color": "#f59e0b"
    },
    {
        "id": "inverted_axis",
        "category": "Cômico & Castigo 😂",
        "title": "Câmera do Caos",
        "desc": "Inverta o eixo X ou Y da câmera nas configurações e tente se orientar!",
        "icon": "🔄",
        "color": "#f59e0b"
    },
    {
        "id": "no_jump",
        "category": "Cômico & Castigo 😂",
        "title": "Pés no Chão",
        "desc": "Proibido usar o botão de pulo a menos que seja 100% obrigatório para prosseguir.",
        "icon": "🚫",
        "color": "#f59e0b"
    },

    # --- Speedrun & Pressão ---
    {
        "id": "sprint_20",
        "category": "Speedrun ⚡",
        "title": "Corrida Contra o Relógio",
        "desc": "Chegue o mais longe possível na campanha em exatos 20 minutos cronometrados.",
        "icon": "⏱️",
        "color": "#10b981"
    },
    {
        "id": "skip_tutorials",
        "category": "Speedrun ⚡",
        "title": "Zero Tutoriais",
        "desc": "Pule imediatamente qualquer tutorial e aprenda os controles apertando botões na marra!",
        "icon": "⏩",
        "color": "#10b981"
    },
    {
        "id": "pacifist_start",
        "category": "Speedrun ⚡",
        "title": "Diplomata Pacifista",
        "desc": "Desvie de todos os inimigos comuns sem atacá-los até o primeiro chefe obrigatório.",
        "icon": "🕊️",
        "color": "#10b981"
    },

    # --- Chat Interativo ---
    {
        "id": "chat_driver",
        "category": "Chat ao Vivo 🗳️",
        "title": "Chat no Comando",
        "desc": "Toda escolha de rota, diálogo ou build deve ser decidida pelo chat da transmissão!",
        "icon": "🎮",
        "color": "#6366f1"
    },
    {
        "id": "sub_names",
        "category": "Chat ao Vivo 🗳️",
        "title": "Tributo aos Inscritos",
        "desc": "Nomeie seus companheiros de equipe, mascotes ou saves com o nome de membros do chat.",
        "icon": "⭐",
        "color": "#6366f1"
    }
]

_ACTIVE_CHALLENGE: Optional[Dict] = None


def get_random_challenge() -> Dict:
    """Returns a random streamer challenge from the roster."""
    return random.choice(CHALLENGES)


def set_active_challenge(challenge: Optional[Dict]):
    """Sets the current active challenge and syncs with Web Overlay."""
    global _ACTIVE_CHALLENGE
    _ACTIVE_CHALLENGE = challenge
    try:
        from aesgard.web_overlay import update_overlay_challenge
        if challenge:
            update_overlay_challenge(challenge.get("title", ""), challenge.get("desc", ""), challenge.get("icon", "🎯"))
        else:
            update_overlay_challenge("", "", "")
    except Exception as e:
        logger.debug(f"Could not broadcast challenge to web overlay: {e}")


def get_active_challenge() -> Optional[Dict]:
    """Gets current active challenge or None."""
    global _ACTIVE_CHALLENGE
    return _ACTIVE_CHALLENGE


def clear_challenge():
    """Clears current active challenge."""
    set_active_challenge(None)
