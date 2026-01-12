# Janela deslizante (deque) + progress (X/Y) + controle de tamanho
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bot.storage.state import BotState


def _parse_time(value: Any) -> Optional[datetime]:
    """
    Tenta converter o campo time pra datetime.
    Aceita:
    - "YYYY-MM-DD HH:MM:SS" (ideal)
    - formato original do Pragmatic: "%b %d, %Y %I:%M:%S %p"
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value

    s = str(value).strip()
    if not s:
        return None

    # 1) formato ISO-like
    try:
        # "2026-01-12 14:33:12"
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # 2) formato original (ex: "Jan 12, 2026 02:33:12 PM")
    try:
        return datetime.strptime(s, "%b %d, %Y %I:%M:%S %p")
    except ValueError:
        return None


def _time_key(result: Dict[str, Any]) -> Tuple[int, str]:
    """
    Chave de ordenação estável:
    - primeiro: timestamp (se der pra parsear)
    - segundo: gameId (pra desempate)
    """
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
    Recebe uma lista/iterável de resultados vindos do WS.
    - dedup por gameId
    - ordena por time (quando possível)
    - adiciona no deque (janela deslizante)
    Retorna quantos resultados NOVOS foram adicionados.
    """
    items: List[Dict[str, Any]] = list(incoming or [])
    if not items:
        return 0

    items.sort(key=_time_key)

    added = 0
    for r in items:
        gid = _normalize_game_id(r.get("gameId"))
        if gid is None:
            continue

        if gid in state.seen_game_ids:
            continue

        # marca como visto
        state.seen_game_ids.add(gid)

        # adiciona na janela
        state.results.append(r)
        added += 1

    # Anti-"set infinito": de tempos em tempos, rebaseia o set a partir do deque
    # (assim ele fica no tamanho da janela e não cresce pra sempre)
    if len(state.seen_game_ids) > max(200, state.window_size * 3):
        state.seen_game_ids = {str(x.get("gameId")) for x in state.results if x.get("gameId") is not None}

    return added


def current_window_label(state: BotState) -> int:
    """
    Enquanto ainda não completou a janela, usamos o número atual (ex: 20, 33).
    Quando completa, usamos o tamanho total da janela (ex: 40).
    """
    return state.window_size if len(state.results) >= state.window_size else len(state.results)


def last_n_results(state: BotState) -> List[Dict[str, Any]]:
    """
    Retorna uma lista com os resultados atuais na janela (na ordem já mantida).
    """
    return list(state.results)
