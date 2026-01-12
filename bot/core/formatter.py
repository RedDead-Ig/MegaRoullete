# Monta o texto do relatório no formato final (com espaçamento premium)
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from bot.core.analytics import compute_analytics, get_cor
from bot.core.buffer import current_window_label, last_n_results
from bot.storage.state import BotState
from bot.telegram import texts


ROULETTE_NAME = "Mega Roulette Multiplicadora"


def _chunk(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _grid_numbers(nums: List[int], per_row: int = 5) -> str:
    """
    Monta grid monoespaçado “ok” pro Telegram.
    Ex: 12  0  34  7  19
    """
    rows = _chunk(nums, per_row)
    lines = []
    for row in rows:
        # alinhamento simples: número com largura 2 (0..36), mas sem ficar travado demais
        line = "  ".join(f"{n:>2}" for n in row)
        lines.append(line)
    return "\n".join(lines) if lines else "—"


def _grid_colors(nums: List[int], per_row: int = 5) -> str:
    """
    Transforma números em emojis de cor.
    Vermelho 🔴 | Preto ⚫ | Zero 🟢
    """
    def to_emoji(n: int) -> str:
        if n == 0:
            return "🟢"
        return "🔴" if get_cor(n) == "Vermelho" else "⚫"

    rows = _chunk(nums, per_row)
    lines = []
    for row in rows:
        lines.append(" ".join(to_emoji(n) for n in row))
    return "\n".join(lines) if lines else "—"


def _extract_numbers(results: List[Dict[str, Any]]) -> List[int]:
    nums: List[int] = []
    for r in results:
        v = r.get("result", r.get("number"))
        try:
            nums.append(int(v))
        except (TypeError, ValueError):
            continue
    return nums


def render_report(state: BotState) -> str:
    """
    Renderiza a mensagem COMPLETA do bot (a que será editada).
    """
    now = datetime.now()
    date_str = texts.fmt_date_br(now)

    results = last_n_results(state)
    nums = _extract_numbers(results)

    # janela “visível” enquanto não completou
    visible_window = current_window_label(state)
    ready = len(results) >= state.window_size

    # título em execução
    title = texts.running_title_block(window=state.window_size, ready=ready)

    # progresso
    progress = texts.loading_block(
        progress_bar=state.progress_bar(20),
        count=state.progress_count(),
        window=state.window_size,
        percent=state.progress_percent(),
    )

    # grids (mostra a janela atual, não necessariamente cheia)
    numbers_grid = _grid_numbers(nums, per_row=5)
    colors_grid = _grid_colors(nums, per_row=5)

    numbers = texts.numbers_block("ÚLTIMOS NÚMEROS", numbers_grid, total=len(nums))
    colors = texts.colors_block("CORES", colors_grid, total=len(nums))

    # analytics em cima do que temos (até completar)
    analytics = compute_analytics(results, window=visible_window)

    counts = texts.count_block(
        window=visible_window,
        pares=analytics.pares,
        impares=analytics.impares,
        zeros=analytics.zeros,
        vermelhos=analytics.vermelhos,
        pretos=analytics.pretos,
        verdes=analytics.verdes,
        baixos=analytics.baixos,
        altos=analytics.altos,
    )

    dom = texts.dominance_block(
        window=visible_window,
        duzia=analytics.duzia_predominante,
        coluna=analytics.coluna_predominante,
    )

    # header + tudo
    msg = texts.header_block(ROULETTE_NAME, date_str)
    msg += "\n\n" + title
    msg += progress
    msg += numbers
    msg += colors
    msg += counts
    msg += dom

    # status WS (se quiser mostrar discretamente)
    if not state.ws_connected and state.ws_last_error:
        msg += texts.error_block(f"WS offline: {state.ws_last_error}")

    return msg
