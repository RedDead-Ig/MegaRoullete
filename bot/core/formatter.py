from __future__ import annotations

from typing import Any, Dict, List, Optional

from bot.core.analytics import compute_analytics, get_cor
from bot.core.buffer import current_window_label, last_n_results
from bot.storage.state import BotState
from bot.telegram import texts


ROULETTE_NAME = "Mega Roulette Multiplicadora"


def _chunk(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _grid_numbers(nums: List[int], per_row: int = 5) -> str:
    rows = _chunk(nums, per_row)
    if not rows:
        return "—"
    lines = []
    for row in rows:
        lines.append("  ".join(f"{n:>2}" for n in row))
    return "\n".join(lines)


def _grid_colors(nums: List[int], per_row: int = 5) -> str:
    def to_emoji(n: int) -> str:
        if n == 0:
            return "🟢"
        return "🔴" if get_cor(n) == "Vermelho" else "⚫"

    rows = _chunk(nums, per_row)
    if not rows:
        return "—"
    return "\n".join(" ".join(to_emoji(n) for n in row) for row in rows)


def _extract_numbers(results: List[Dict[str, Any]]) -> List[int]:
    out: List[int] = []
    for r in results:
        try:
            n = int(r.get("result", r.get("number")))
        except Exception:
            continue
        if 0 <= n <= 36:
            out.append(n)
    return out


def render_report(state: BotState) -> str:
    # horário e data CERTOS (UTC−3)
    date_str = texts.fmt_date_br()

    results = last_n_results(state)
    nums = _extract_numbers(results)

    visible_window = current_window_label(state)  # 0..window_size
    ready = len(results) >= state.window_size

    header = texts.header_block(ROULETTE_NAME, date_str)
    updated = texts.updated_time_block()

    status = texts.status_block(total_games=state.total_games, window_size=state.window_size)

    progress = texts.loading_block(
        progress_bar=state.progress_bar(20),
        count=state.progress_count(),
        window=state.window_size,
        percent=state.progress_percent(),
    )

    numbers = texts.numbers_block(_grid_numbers(nums, 5), total=len(nums))
    colors = texts.colors_block(_grid_colors(nums, 5), total=len(nums))

    analytics = compute_analytics(results, window_label=visible_window)

    contagem = texts.count_block(
        window=visible_window,
        total_games=state.total_games,
        pares=analytics.pares, pct_pares=analytics.pct_pares,
        impares=analytics.impares, pct_impares=analytics.pct_impares,
        vermelhos=analytics.vermelhos, pct_vermelhos=analytics.pct_vermelhos,
        pretos=analytics.pretos, pct_pretos=analytics.pct_pretos,
        baixos=analytics.baixos, pct_baixos=analytics.pct_baixos,
        altos=analytics.altos, pct_altos=analytics.pct_altos,
    )

    zeros = texts.zeros_block(window=visible_window, zeros=analytics.zeros, pct_zeros=analytics.pct_zeros)

    duzias = texts.dominance_duzias_block(window=visible_window, items=analytics.duzias_rank)
    colunas = texts.dominance_colunas_block(window=visible_window, items=analytics.colunas_rank)
    regioes = texts.region_rank_block(window=visible_window, items=analytics.regioes_rank)

    footer = texts.footer_block(total_games=state.total_games, last_number=state.last_number)

    msg = (
        header
        + updated
        + status
        + progress
        + numbers
        + colors
        + contagem
        + zeros
        + duzias
        + colunas
        + regioes
        + footer
    )

    # se WS estiver caído, mostra uma linha (discreta) no final
    if (not state.ws_connected) and state.ws_last_error:
        msg += f"\n⚠️ WS offline: {state.ws_last_error}\n"

    return msg
