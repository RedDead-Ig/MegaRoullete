import os
from typing import Optional


def _get_int(name: str, default: Optional[int] = None) -> Optional[int]:
    """Lê env var inteira. Se não existir, volta default."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value.strip())
    except ValueError:
        raise ValueError(f"Variável {name} precisa ser um inteiro. Valor recebido: {value!r}")


# ===== Telegram =====
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID: Optional[int] = _get_int("ADMIN_CHAT_ID", None)  # opcional (recomendado)

# ===== WebSocket / Mesa =====
ROULETTE_WS_URL: str = os.getenv("ROULETTE_WS_URL", "wss://dga.pragmaticplaylive.net/ws").strip()
CASINO_ID: str = os.getenv("CASINO_ID", "ppcdk00000005349").strip()
CURRENCY: str = os.getenv("CURRENCY", "BRL").strip()
TABLE_KEY: int = _get_int("TABLE_KEY", 204)  # pragmatic: key da mesa

# ===== Janela de análise =====
DEFAULT_WINDOW_SIZE: int = _get_int("DEFAULT_WINDOW_SIZE", 40)
WINDOW_MIN: int = _get_int("WINDOW_MIN", 20)
WINDOW_MAX: int = _get_int("WINDOW_MAX", 200)

# ===== Rate limit (pra não tomar flood do Telegram) =====
# editar 1x por resultado costuma ser ok, mas se o WS vier “em rajada” ajuda ter um mínimo
MIN_SECONDS_BETWEEN_EDITS: float = float(os.getenv("MIN_SECONDS_BETWEEN_EDITS", "0.8"))


def is_admin(chat_id: int) -> bool:
    """Se ADMIN_CHAT_ID estiver setado, só deixa esse chat usar o bot."""
    return (ADMIN_CHAT_ID is None) or (chat_id == ADMIN_CHAT_ID)


def validate_window_size(n: int) -> int:
    if n < WINDOW_MIN:
        return WINDOW_MIN
    if n > WINDOW_MAX:
        return WINDOW_MAX
    return n
