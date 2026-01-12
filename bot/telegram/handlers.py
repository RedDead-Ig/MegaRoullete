from __future__ import annotations

import os
from typing import List, Optional


# =========================
# HELPERS
# =========================
def _get_env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip()


def _get_int(name: str, default: int) -> int:
    raw = _get_env(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw = _get_env(name, str(default))
    try:
        return float(raw)
    except ValueError:
        return default


def _parse_admin_ids(raw: str) -> List[int]:
    """
    Aceita:
      ADMIN_CHAT_ID="123"
      ADMIN_CHAT_ID="123,456,789"
      ADMIN_CHAT_ID=" 123  ,  456 "
    """
    raw = (raw or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    out: List[int] = []
    for p in parts:
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            continue
    return out


# =========================
# ENV (Railway Variables)
# =========================
TELEGRAM_BOT_TOKEN: str = _get_env("TELEGRAM_BOT_TOKEN", "")

ROULETTE_WS_URL: str = _get_env("ROULETTE_WS_URL", "wss://dga.pragmaticplaylive.net/ws")
CASINO_ID: str = _get_env("CASINO_ID", "ppcdk00000005349")
CURRENCY: str = _get_env("CURRENCY", "BRL")
TABLE_KEY: int = _get_int("TABLE_KEY", 204)

# Admin
_ADMIN_RAW = _get_env("ADMIN_CHAT_ID", "")
ADMIN_CHAT_IDS: List[int] = _parse_admin_ids(_ADMIN_RAW)

# Janela
WINDOW_MIN: int = 5          # ✅ agora é 5
WINDOW_MAX: int = 200        # pode subir se quiser, mas 200 já é seguro

DEFAULT_WINDOW_SIZE: int = _get_int("DEFAULT_WINDOW_SIZE", 40)
DEFAULT_WINDOW_SIZE = max(WINDOW_MIN, min(WINDOW_MAX, DEFAULT_WINDOW_SIZE))

# Anti-spam de edição (mensagem fixa)
MIN_SECONDS_BETWEEN_EDITS: float = _get_float("MIN_SECONDS_BETWEEN_EDITS", 1.2)


# =========================
# API / Bot Rules
# =========================
def is_admin(chat_id: int) -> bool:
    # Se você não setou ADMIN_CHAT_ID, deixa tudo bloqueado por segurança
    if not ADMIN_CHAT_IDS:
        return False
    return int(chat_id) in ADMIN_CHAT_IDS


def validate_window_size(n: int) -> int:
    """
    Normaliza a janela pro range permitido.
    Agora aceita a partir de 5.
    """
    try:
        n = int(n)
    except Exception:
        return DEFAULT_WINDOW_SIZE

    if n < WINDOW_MIN:
        return WINDOW_MIN
    if n > WINDOW_MAX:
        return WINDOW_MAX
    return n


def typical_window_values() -> List[int]:
    """
    Só pra mostrar sugestões no /help e /configurar_janela
    (pode ajustar se quiser).
    """
    return [5, 10, 20, 40, 60, 80, 100]
