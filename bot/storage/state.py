# Estado do bot (message_id, chat_id, running, window_size, caches)
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Deque, Dict, Any, List, Set
from collections import deque
import time


@dataclass
class BotState:
    # controle básico
    running: bool = False

    # onde o bot está “fixado” (mensagem editável)
    chat_id: Optional[int] = None
    message_id: Optional[int] = None

    # janela e dados
    window_size: int = 40
    results: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=40))
    seen_game_ids: Set[str] = field(default_factory=set)

    # anti-spam / performance
    last_render_text: str = ""
    last_edit_ts: float = 0.0

    # status de conexão
    ws_connected: bool = False
    ws_last_error: Optional[str] = None
    ws_last_msg_ts: float = 0.0

    def set_window_size(self, n: int) -> None:
        """Atualiza janela e ajusta o deque sem perder o que for possível."""
        self.window_size = n
        old = list(self.results)
        self.results = deque(old[-n:], maxlen=n)

        # Recria o set baseado no que ficou (pra não crescer infinito)
        self.seen_game_ids = {str(r.get("gameId")) for r in self.results if r.get("gameId") is not None}

    def reset_history(self) -> None:
        """Limpa histórico (quando você quiser recomeçar do zero)."""
        self.results.clear()
        self.seen_game_ids.clear()

    def progress_count(self) -> int:
        """Quantos resultados já temos na janela (até completar window_size)."""
        return min(len(self.results), self.window_size)

    def progress_percent(self) -> int:
        if self.window_size <= 0:
            return 0
        return int((self.progress_count() / self.window_size) * 100)

    def progress_bar(self, width: int = 20) -> str:
        """Barra estilo ███░░, boa pra Telegram."""
        if self.window_size <= 0:
            return "░" * width
        filled = int((self.progress_count() / self.window_size) * width)
        filled = max(0, min(width, filled))
        return ("█" * filled) + ("░" * (width - filled))

    def can_edit_now(self, min_seconds_between_edits: float) -> bool:
        """Rate limit: evita flood de edit."""
        now = time.time()
        return (now - self.last_edit_ts) >= float(min_seconds_between_edits)

    def mark_edited(self, new_text: str) -> None:
        """Marca que editou com sucesso."""
        self.last_render_text = new_text
        self.last_edit_ts = time.time()

    def set_fixed_message(self, chat_id: int, message_id: int) -> None:
        self.chat_id = chat_id
        self.message_id = message_id
