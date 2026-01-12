from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bot.storage.state import BotState


def _parse_time(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value

    s = str(value).strip()
    if not s:
        return None

    # formato já normalizado
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # fallback formato original
    try:
        return datetime.strptime(s, "%b %d, %Y %I:%M:%S %p")
    except ValueError:
        return None


def _time_key(result: Dict[str, Any]) -> Tuple[int, str]:
    dt = _parse_time(result.get("time"))
    ts = int(dt.timestamp()) if dt else 0
    gid = str(result.get("gameId", ""))
    return (ts, gid)


def _normalize_game_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


# ✅ ESSA FUNÇÃO TEM QUE EXISTIR (é ela que o main.py importa)
def add_results(state: BotState, incoming: Iterable[Dict[str, Any]]) -> int:
    """
    - dedup por gameId
    - ordena por time
    - adiciona na janela
    - incrementa total_games
    - atualiza last_number
    """
    items: List[Dict[str, Any]] = list(incoming or [])
    if not items:
        return 0

    items.sort(key=_time_key)

    added = 0
    last_num: Optional[int] = None

    for r in items:
        gid = _normalize_game_id(r.get("gameId"))
        if gid is None:
            continue

        if gid in state.seen_game_ids:
            continue

        state.seen_game_ids.add(gid)
        state.results.append(r)
        added += 1

        try:
            last_num = int(r.get("result", r.get("number")))
        except Exception:
            pass

    if added > 0:
        state.total_games += added
        if last_num is not None:
            state.last_number = last_num

    # Anti-set infinito
    if len(state.seen_game_ids) > max(200, state.window_size * 3):
        state.seen_game_ids = {str(x.get("gameId")) for x in state.results if x.get("gameId") is not None}

    return added


def current_window_label(state: BotState) -> int:
    return state.window_size if len(state.results) >= state.window_size else len(state.results)


def last_n_results(state: BotState) -> List[Dict[str, Any]]:
    return list(state.results)
