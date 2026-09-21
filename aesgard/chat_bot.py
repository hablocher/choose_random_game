# -*- coding: utf-8 -*-
"""
Native Live Chat Bot (Twitch IRC) for Choose Random Game.
Connects anonymously to Twitch chat (0 token required for read-only)
to automatically compute live community votes (!voto 1, !voto 2, !voto 3)
and synchronize with the OBS Web Overlay in real time.
"""
import ssl
import time
import socket
import logging
import threading
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class TwitchChatBot(QObject):
    """
    Background worker that connects to Twitch IRC over SSL to listen for community votes.
    Uses anonymous JustinFan credentials (no OAuth token required to read votes!).
    """
    vote_received = pyqtSignal(int, str)  # (option_index 0-2, username)
    status_changed = pyqtSignal(bool, str) # (connected, message)

    def __init__(self, channel: str = "", parent=None):
        super().__init__(parent)
        self.channel = channel.lower().lstrip("#").strip()
        self._running = False
        self._socket: Optional[ssl.SSLSocket] = None
        self._thread: Optional[threading.Thread] = None

    def start_bot(self, channel: Optional[str] = None):
        """Starts listening to the specified Twitch channel."""
        if channel:
            self.channel = channel.lower().lstrip("#").strip()
        if not self.channel:
            self.status_changed.emit(False, "Canal da Twitch não configurado.")
            return

        if self._running:
            self.stop_bot()

        self._running = True
        self._thread = threading.Thread(target=self._run_irc_loop, daemon=True)
        self._thread.start()

    def stop_bot(self):
        """Stops the IRC connection."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self.status_changed.emit(False, "Desconectado do chat.")

    def is_connected(self) -> bool:
        return self._running and self._socket is not None

    def _run_irc_loop(self):
        server = "irc.chat.twitch.tv"
        port = 6697
        nick = f"justinfan{int(time.time() % 89999 + 10000)}"

        try:
            self.status_changed.emit(False, f"Conectando ao chat de #{self.channel}...")
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(10.0)

            context = ssl.create_default_context()
            self._socket = context.wrap_socket(raw_sock, server_hostname=server)
            self._socket.connect((server, port))

            # Send Anonymous IRC login
            self._socket.send(f"PASS oauth:fake\r\n".encode("utf-8"))
            self._socket.send(f"NICK {nick}\r\n".encode("utf-8"))
            self._socket.send(f"JOIN #{self.channel}\r\n".encode("utf-8"))

            self._socket.settimeout(2.0)
            self.status_changed.emit(True, f"Conectado ao vivo em #{self.channel}!")
            logger.info(f"Twitch Chat Bot connected to #{self.channel}")

            buffer = ""
            while self._running:
                try:
                    data = self._socket.recv(2048).decode("utf-8", errors="ignore")
                    if not data:
                        break
                    buffer += data
                    lines = buffer.split("\r\n")
                    buffer = lines.pop()

                    for line in lines:
                        # Respond to Twitch PING keep-alive
                        if line.startswith("PING"):
                            self._socket.send(f"PONG {line.split()[1]}\r\n".encode("utf-8"))
                            continue

                        # Parse PRIVMSG
                        if "PRIVMSG" in line:
                            self._handle_privmsg(line)

                except socket.timeout:
                    continue
                except Exception as e:
                    if self._running:
                        logger.debug(f"IRC read notice: {e}")
                    break

        except Exception as e:
            logger.warning(f"Error connecting to Twitch IRC: {e}")
            self.status_changed.emit(False, f"Erro de conexão: {e}")
        finally:
            self._running = False
            self.status_changed.emit(False, "Desconectado.")

    def _handle_privmsg(self, raw_line: str):
        """Parses chat messages looking for vote commands."""
        try:
            # Format: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
            parts = raw_line.split("PRIVMSG", 1)
            if len(parts) < 2:
                return

            user_part = parts[0]
            username = user_part.split("!")[0].lstrip(":") if "!" in user_part else "viewer"

            msg_part = parts[1].split(":", 1)
            if len(msg_part) < 2:
                return
            msg = msg_part[1].strip().lower()

            # Check vote patterns
            # Matches: "!voto 1", "!voto 2", "!voto 3", "!1", "!2", "!3", "1", "2", "3"
            vote_idx = -1
            if msg in ("!voto 1", "!1", "1"):
                vote_idx = 0
            elif msg in ("!voto 2", "!2", "2"):
                vote_idx = 1
            elif msg in ("!voto 3", "!3", "3"):
                vote_idx = 2

            if vote_idx >= 0:
                logger.info(f"Chat vote received from @{username}: Option {vote_idx + 1}")
                self.vote_received.emit(vote_idx, username)

                # Automatically record vote in Web Overlay
                try:
                    from aesgard.web_overlay import record_poll_vote
                    record_poll_vote(vote_idx)
                except Exception as ex:
                    logger.debug(f"Could not record vote in web overlay: {ex}")

        except Exception as e:
            logger.debug(f"Error parsing PRIVMSG: {e}")


_GLOBAL_CHAT_BOT: Optional[TwitchChatBot] = None


def get_chat_bot() -> TwitchChatBot:
    """Returns singleton TwitchChatBot instance."""
    global _GLOBAL_CHAT_BOT
    if _GLOBAL_CHAT_BOT is None:
        _GLOBAL_CHAT_BOT = TwitchChatBot()
    return _GLOBAL_CHAT_BOT
