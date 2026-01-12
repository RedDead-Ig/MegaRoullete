from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Deque, Dict, Any, Set
from collections import deque
import time


# Quantos IDs a gente guarda pra deduplicar globalmente (sessão do bot).
# 10k é bem tranquilo e evita “recontar” ao trocar janela.
SEEN_IDS_MAX = 10_000


@dataclass
class BotState:
    running: bool = False

    # mensagem fixa editável
    chat_id: Optional[int] = None
    message_id: Optional[int] = None

    # janela e dados
    window_size: int = 40
    results: Deque[Dict[str, Any]] = field(default_factory=deque)

    # ✅ dedup GLOBAL (não depende da janela)
    seen_game_ids: Set[str] = field(default_factory=set)
    seen_game_ids_queue: Deque[str] = field(default_factory=deque)

    # acumulados desde que o processo iniciou
    total_games: int = 0
    last_number: Optional[int] = None

    # modo “esperando o usuário mandar 20”
    awaiting_window_size: bool = False
    awaiting_window_size_chat_id: Optional[int] = None

    # anti-spam / performance
    last_render_text: str = ""
    last_edit_ts: float = 0.0

    # status WS
    ws_connected: bool = False
    ws_last_error: Optional[str] = None
    ws_last_msg_ts: float = 0.0

    def __post_init__(self) -> None:
        # garante maxlen alinhado ao window_size desde o início
        if not isinstance(self.results, deque) or self.results.maxlen != self.window_size:
            self.results = deque(list(self.results), maxlen=self.window_size)

    def set_window_size(self, n: int) -> None:
        """Atualiza janela sem resetar dedup global."""
        self.window_size = n
        old = list(self.results)
        self.results = deque(old[-n:], maxlen=n)
        # ⚠️ NÃO mexe no seen_game_ids aqui (senão reconta IDs antigos)

    def reset_history(self) -> None:
        """Limpa histórico visível e dedup (use só se você REALMENTE quiser zerar a sessão)."""
        self.results.clear()
        self.seen_game_ids.clear()
        self.seen_game_ids_queue.clear()
        self.total_games = 0
        self.last_number = None

    def progress_count(self) -> int:
        return min(len(self.results), self.window_size)

    def progress_percent(self) -> int:
        if self.window_size <= 0:
            return 0
        return int((self.progress_count() / self.window_size) * 100)

    def progress_bar(self, width: int = 20) -> str:
        if self.window_size <= 0:
            return "░" * width
        filled = int((self.progress_count() / self.window_size) * width)
        filled = max(0, min(width, filled))
        return ("█" * filled) + ("░" * (width - filled))

    def can_edit_now(self, min_seconds_between_edits: float) -> bool:
        now = time.time()
        return (now - self.last_edit_ts) >= float(min_seconds_between_edits)

    def mark_edited(self, new_text: str) -> None:
        self.last_render_text = new_text
        self.last_edit_ts = time.time()

    def set_fixed_message(self, chat_id: int, message_id: int) -> None:
        self.chat_id = chat_id
        self.message_id = message_id
