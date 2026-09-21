# -*- coding: utf-8 -*-
"""
Local Web Server and OBS Studio Browser Source Overlay for Choose Random Game.
Serves responsive, animated HTML5 glassmorphism HUD overlays on http://localhost:8089/overlay
and interactive poll widgets on http://localhost:8089/overlay/poll
"""
import os
import json
import base64
import logging
import threading
from io import BytesIO
from typing import Optional, Dict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

DEFAULT_PORT = 8089

_OVERLAY_STATE = {
    "title": "Nenhum Jogo Selecionado",
    "platform": "PC",
    "platform_color": "#0984e3",
    "status": "🎲 SORTEADOR DE JOGOS",
    "hltb": "",
    "cover_base64": "",
    "timer_text": "00:00:00",
    "is_playing": False,
    "channel_handle": "@ChooseRandomGame",
    "challenge": {
        "active": False,
        "title": "",
        "desc": "",
        "icon": "🎯"
    },
    "poll": {
        "active": False,
        "question": "Qual jogo devemos jogar a seguir?",
        "options": [
            {"title": "Opção 1", "platform": "PC", "votes": 0, "pct": 0},
            {"title": "Opção 2", "platform": "PC", "votes": 0, "pct": 0},
            {"title": "Opção 3", "platform": "PC", "votes": 0, "pct": 0}
        ],
        "total_votes": 0
    }
}

_SERVER_INSTANCE: Optional[HTTPServer] = None
_SERVER_THREAD: Optional[threading.Thread] = None

def update_overlay_game(title: str, platform: str = "Retro", hltb_text: str = "", cover_pixmap=None, platform_color: str = "#00cec9", status: str = "🎲 SORTEADO"):
    """Updates the active game state for the OBS overlay."""
    _OVERLAY_STATE["title"] = title
    _OVERLAY_STATE["platform"] = platform
    _OVERLAY_STATE["platform_color"] = platform_color
    _OVERLAY_STATE["hltb"] = hltb_text
    _OVERLAY_STATE["status"] = status
    
    if cover_pixmap is not None:
        try:
            from PyQt6.QtCore import QBuffer, QIODevice
            buf = QBuffer()
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            cover_pixmap.save(buf, "PNG")
            b64 = base64.b64encode(buf.data().data()).decode("utf-8")
            _OVERLAY_STATE["cover_base64"] = f"data:image/png;base64,{b64}"
            buf.close()
        except Exception as e:
            logger.debug(f"Error encoding cover to base64 for overlay: {e}")

def update_overlay_timer(timer_str: str, is_playing: bool = True):
    """Updates the live gameplay timer on the overlay."""
    _OVERLAY_STATE["timer_text"] = timer_str
    _OVERLAY_STATE["is_playing"] = is_playing
    if is_playing:
        _OVERLAY_STATE["status"] = "🎮 EM JOGO NA LIVE"

def update_overlay_channel(channel_handle: str):
    """Updates the channel name/handle shown on the overlay."""
    _OVERLAY_STATE["channel_handle"] = channel_handle or "@ChooseRandomGame"

def update_overlay_challenge(title: str = "", desc: str = "", icon: str = "🎯"):
    """Updates the active live challenge shown on the OBS overlay."""
    _OVERLAY_STATE["challenge"] = {
        "active": bool(title),
        "title": title,
        "desc": desc,
        "icon": icon or "🎯"
    }

def update_overlay_poll(*args, **kwargs):
    """
    Updates the interactive chat poll state.
    Supports:
      update_overlay_poll(options_list=[{...}], question="...")
      update_overlay_poll(optA, optB, optC, vA=0, vB=0, vC=0)
    """
    if len(args) == 1 and isinstance(args[0], list):
        options_list = args[0]
        question = kwargs.get("question", "Qual jogo jogar a seguir?")
    elif len(args) >= 3 and isinstance(args[0], str):
        vA = args[3] if len(args) > 3 else 0
        vB = args[4] if len(args) > 4 else 0
        vC = args[5] if len(args) > 5 else 0
        options_list = [
            {"title": args[0], "platform": "A", "votes": vA},
            {"title": args[1], "platform": "B", "votes": vB},
            {"title": args[2], "platform": "C", "votes": vC}
        ]
        question = kwargs.get("question", "Qual jogo jogar a seguir?")
    else:
        options_list = kwargs.get("options_list", [])
        question = kwargs.get("question", "Qual jogo jogar a seguir?")

    total = sum(opt.get("votes", 0) for opt in options_list)
    formatted = []
    for opt in options_list:
        v = opt.get("votes", 0)
        pct = round((v / total * 100)) if total > 0 else 0
        formatted.append({
            "title": opt.get("title", ""),
            "platform": opt.get("platform", "Retro"),
            "votes": v,
            "pct": pct
        })
    _OVERLAY_STATE["poll"] = {
        "active": len(formatted) > 0,
        "question": question,
        "options": formatted,
        "total_votes": total
    }

def record_poll_vote(option_idx: int) -> bool:
    """Adds +1 vote to the chosen option (0, 1, or 2)."""
    poll = _OVERLAY_STATE.get("poll", {})
    options = poll.get("options", [])
    if 0 <= option_idx < len(options):
        options[option_idx]["votes"] += 1
        total = sum(opt.get("votes", 0) for opt in options)
        for opt in options:
            opt["pct"] = round((opt["votes"] / total * 100)) if total > 0 else 0
        poll["total_votes"] = total
        return True
    return False

OVERLAY_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OBS Studio Game HUD Overlay</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: transparent;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            overflow: hidden;
            display: flex;
            align-items: flex-end;
            padding: 30px;
            height: 100vh;
            width: 100vw;
        }

        .hud-card {
            background: rgba(13, 15, 20, 0.88);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-left: 4px solid #00cec9;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.65), 0 0 25px rgba(0, 206, 201, 0.2);
            border-radius: 16px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            max-width: 640px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: slideIn 0.8s ease-out;
        }

        @keyframes slideIn {
            from { transform: translateY(80px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .cover-wrap {
            position: relative;
            width: 90px;
            height: 120px;
            border-radius: 10px;
            overflow: hidden;
            flex-shrink: 0;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.15);
            background: #1e272e;
        }

        .cover-wrap img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .info-col {
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex-grow: 1;
            min-width: 0;
        }

        .tag-row {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .status-badge {
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(0, 206, 201, 0.15);
            color: #00cec9;
            border: 1px solid rgba(0, 206, 201, 0.3);
        }

        .platform-badge {
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.8px;
            padding: 3px 8px;
            border-radius: 4px;
            color: #ffffff;
            background-color: #0984e3;
            text-transform: uppercase;
        }

        .hltb-badge {
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(241, 196, 15, 0.15);
            color: #f1c40f;
            border: 1px solid rgba(241, 196, 15, 0.3);
            display: none;
        }

        .game-title {
            font-size: 18px;
            font-weight: 800;
            color: #ffffff;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 480px;
        }

        .footer-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11px;
            color: #8c96a8;
            margin-top: 4px;
        }

        .channel-name {
            font-weight: 600;
            color: #cbd5e1;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .timer-badge {
            font-family: 'Consolas', 'Courier New', monospace;
            font-weight: 700;
            color: #00cec9;
            background: rgba(0, 0, 0, 0.4);
            padding: 2px 6px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="hud-card" id="hudCard">
        <div class="cover-wrap">
            <img id="gameCover" src="" alt="Capa">
        </div>
        <div class="info-col">
            <div class="tag-row">
                <span class="status-badge" id="statusBadge">🎲 SORTEADO</span>
                <span class="platform-badge" id="platformBadge">PC</span>
                <span class="hltb-badge" id="hltbBadge">⏱️ ~15h</span>
            </div>
            <div class="game-title" id="gameTitle">Carregando jogo...</div>
            <div class="challenge-row" id="challengeRow" style="display: none; font-size: 11px; background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; border-radius: 6px; padding: 3px 8px; font-weight: bold; margin-top: 2px;">
                <span id="challengeIcon">🎯</span> <span id="challengeTitle">Desafio</span>
            </div>
            <div class="footer-row">
                <span class="channel-name" id="channelName">📺 Live Stream</span>
                <span class="timer-badge" id="timerBadge">⏱️ 00:00:00</span>
            </div>
        </div>
    </div>

    <script>
        async function fetchState() {
            try {
                const res = await fetch('/api/current');
                if (!res.ok) return;
                const data = await res.json();

                document.getElementById('gameTitle').textContent = data.title || 'Escolhendo Jogo...';
                
                const platBadge = document.getElementById('platformBadge');
                platBadge.textContent = (data.platform || 'PC').toUpperCase();
                platBadge.style.backgroundColor = data.platform_color || '#0984e3';

                document.getElementById('statusBadge').textContent = data.status || '🎲 AO VIVO';
                document.getElementById('channelName').textContent = data.channel_handle || '📺 Live';
                document.getElementById('timerBadge').textContent = '⏱️ ' + (data.timer_text || '00:00:00');

                const hltbBadge = document.getElementById('hltbBadge');
                if (data.hltb) {
                    hltbBadge.textContent = data.hltb;
                    hltbBadge.style.display = 'inline-block';
                } else {
                    hltbBadge.style.display = 'none';
                }

                const chRow = document.getElementById('challengeRow');
                if (data.challenge && data.challenge.active) {
                    chRow.style.display = 'block';
                    document.getElementById('challengeIcon').textContent = data.challenge.icon || '🎯';
                    document.getElementById('challengeTitle').textContent = 'Desafio: ' + data.challenge.title;
                } else {
                    chRow.style.display = 'none';
                }

                const img = document.getElementById('gameCover');
                if (data.cover_base64 && data.cover_base64.length > 50) {
                    img.src = data.cover_base64;
                    img.parentElement.style.display = 'block';
                } else {
                    img.parentElement.style.display = 'none';
                }
            } catch (err) {
                console.warn('Erro ao atualizar overlay:', err);
            }
        }

        setInterval(fetchState, 1200);
        fetchState();
    </script>
</body>
</html>
"""

POLL_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OBS Chat Choice Poll</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: transparent;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            overflow: hidden;
            display: flex;
            align-items: flex-end;
            padding: 30px;
            height: 100vh;
            width: 100vw;
        }

        .poll-box {
            background: rgba(13, 15, 20, 0.92);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-top: 3px solid #6c5ce7;
            border-radius: 14px;
            padding: 16px 20px;
            width: 480px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
        }

        .poll-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .poll-title {
            font-size: 13px;
            font-weight: 800;
            color: #a29bfe;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .poll-votes {
            font-size: 11px;
            color: #8c96a8;
            font-weight: bold;
        }

        .poll-option {
            margin-bottom: 10px;
        }

        .opt-label-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }

        .opt-title {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 380px;
        }

        .opt-pct {
            color: #00cec9;
            font-weight: 800;
        }

        .progress-track {
            height: 8px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #6c5ce7, #00cec9);
            width: 0%;
            transition: width 0.4s ease-out;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="poll-box" id="pollBox">
        <div class="poll-header">
            <span class="poll-title">🗳️ VOTAÇÃO DO CHAT</span>
            <span class="poll-votes" id="totalVotes">0 votos</span>
        </div>
        <div id="optionsContainer">
            <!-- Dynamic options -->
        </div>
    </div>

    <script>
        async function fetchPoll() {
            try {
                const res = await fetch('/api/current');
                if (!res.ok) return;
                const data = await res.json();
                const poll = data.poll || {};
                
                if (!poll.active) {
                    document.getElementById('pollBox').style.display = 'none';
                    return;
                }
                document.getElementById('pollBox').style.display = 'block';
                document.getElementById('totalVotes').textContent = (poll.total_votes || 0) + ' votos';

                const container = document.getElementById('optionsContainer');
                container.innerHTML = '';

                (poll.options || []).forEach((opt, idx) => {
                    const row = document.createElement('div');
                    row.className = 'poll-option';
                    row.innerHTML = `
                        <div class="opt-label-row">
                            <span class="opt-title">${idx + 1}. ${opt.title}</span>
                            <span class="opt-pct">${opt.pct}%</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill" style="width: ${opt.pct}%"></div>
                        </div>
                    `;
                    container.appendChild(row);
                });
            } catch (e) {
                console.warn(e);
            }
        }
        setInterval(fetchPoll, 1500);
        fetchPoll();
    </script>
</body>
</html>
"""

BINGO_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OBS Studio Live Backlog Bingo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: transparent;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            width: 100vw;
        }
        .bingo-card {
            background: rgba(13, 15, 20, 0.90);
            backdrop-filter: blur(14px);
            border: 2px solid rgba(56, 189, 248, 0.4);
            border-radius: 16px;
            padding: 16px;
            width: 380px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.7);
        }
        .bingo-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .bingo-title {
            font-size: 13px;
            font-weight: 800;
            color: #38bdf8;
            letter-spacing: 1px;
        }
        .bingo-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
        }
        .cell {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 8px 6px;
            font-size: 10px;
            font-weight: 600;
            color: #cbd5e1;
            text-align: center;
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        .cell.marked {
            background: linear-gradient(135deg, #059669, #10b981);
            border-color: #34d399;
            color: #ffffff;
            font-weight: 800;
            transform: scale(0.97);
            box-shadow: 0 0 12px rgba(52, 211, 153, 0.4);
        }
        .winner-banner {
            display: none;
            text-align: center;
            margin-top: 10px;
            font-size: 12px;
            font-weight: 800;
            color: #fbbf24;
            letter-spacing: 1px;
            animation: pulse 1s infinite alternate;
        }
        @keyframes pulse { from { opacity: 0.7; } to { opacity: 1; } }
    </style>
</head>
<body>
    <div class="bingo-card" id="bingoCard">
        <div class="bingo-header">
            <span class="bingo-title">🎯 BINGO DO BACKLOG</span>
            <span style="font-size: 10px; color: #94a3b8;">AO VIVO</span>
        </div>
        <div class="bingo-grid" id="gridContainer"></div>
        <div class="winner-banner" id="winnerBanner">🎉 BINGO COMPLETO! LINHA FEITA!</div>
    </div>
    <script>
        async function updateBingo() {
            try {
                const res = await fetch('/api/bingo');
                if (!res.ok) return;
                const data = await res.json();
                const container = document.getElementById('gridContainer');
                container.innerHTML = '';
                (data.cells || []).forEach(c => {
                    const el = document.createElement('div');
                    el.className = 'cell' + (c.marked ? ' marked' : '');
                    el.textContent = (c.marked ? '✔ ' : '') + c.text;
                    container.appendChild(el);
                });
                document.getElementById('winnerBanner').style.display = data.has_won ? 'block' : 'none';
            } catch (e) {
                console.warn(e);
            }
        }
        setInterval(updateBingo, 1500);
        updateBingo();
    </script>
</body>
</html>
"""

class OverlayHTTPHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the OBS overlay, Bingo widget and API."""

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging in terminal
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/overlay":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(OVERLAY_HTML.encode("utf-8"))

        elif path == "/overlay/poll":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(POLL_HTML.encode("utf-8"))

        elif path == "/bingo" or path == "/overlay/bingo":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(BINGO_HTML.encode("utf-8"))

        elif path == "/api/current":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(_OVERLAY_STATE).encode("utf-8"))

        elif path == "/api/bingo":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            from aesgard.bingo import get_bingo_state
            self.wfile.write(json.dumps(get_bingo_state().to_dict()).encode("utf-8"))

        elif path == "/api/vote":
            params = parse_qs(parsed.query)
            opt_idx = int(params.get("option", ["1"])[0]) - 1
            success = record_poll_vote(opt_idx)
            self.send_response(200 if success else 400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "poll": _OVERLAY_STATE["poll"]}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def start_overlay_server(port: int = DEFAULT_PORT) -> HTTPServer:
    """Starts the OBS overlay HTTP server in a background daemon thread."""
    global _SERVER_INSTANCE, _SERVER_THREAD
    if _SERVER_INSTANCE is not None:
        return _SERVER_INSTANCE

    try:
        _SERVER_INSTANCE = HTTPServer(("localhost", port), OverlayHTTPHandler)
        _SERVER_THREAD = threading.Thread(target=_SERVER_INSTANCE.serve_forever, daemon=True)
        _SERVER_THREAD.start()
        logger.info(f"OBS Web Overlay server running at http://localhost:{port}/overlay")
        return _SERVER_INSTANCE
    except Exception as e:
        logger.warning(f"Could not start Web Overlay server on port {port}: {e}")
        return None

def stop_overlay_server():
    """Shuts down the overlay HTTP server."""
    global _SERVER_INSTANCE
    if _SERVER_INSTANCE:
        try:
            _SERVER_INSTANCE.shutdown()
            _SERVER_INSTANCE = None
        except Exception:
            pass
