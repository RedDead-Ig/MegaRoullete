from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bot.storage.state import BotState, SEEN_IDS_MAX


def _parse_time(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value

    s = str(value).strip()
    if not s:
        return None

    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

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


def add_results(state: BotState, incoming: Iterable[Dict[str, Any]]) -> int:
    """
    Dedup GLOBAL por gameId:
    - se o websocket re-enviar resultados antigos, NÃO aumenta total_games
    - trocar window_size NÃO reseta dedup
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

        # ✅ dedup global
        if gid in state.seen_game_ids:
            continue

        state.seen_game_ids.add(gid)
        state.seen_game_ids_queue.append(gid)

        # cap de memória (remove os mais antigos do set)
        while len(state.seen_game_ids_queue) > SEEN_IDS_MAX:
            old = state.seen_game_ids_queue.popleft()
            state.seen_game_ids.discard(old)

        # adiciona na janela visível (deque já controla maxlen)
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

    return added


def current_window_label(state: BotState) -> int:
    return state.window_size if len(state.results) >= state.window_size else len(state.results)


def last_n_results(state: BotState) -> List[Dict[str, Any]]:
    return list(state.results)
