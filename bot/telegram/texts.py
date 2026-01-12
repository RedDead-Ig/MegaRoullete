from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

import pytz

from bot.core.analytics import RankItem


TZ_NAME = "America/Sao_Paulo"


def now_sp() -> datetime:
    tz = pytz.timezone(TZ_NAME)
    return datetime.now(tz)


def fmt_date_br(dt: Optional[datetime] = None) -> str:
    dt = dt or now_sp()
    return dt.strftime("%d/%m/%Y")


def fmt_time_br(dt: Optional[datetime] = None) -> str:
    dt = dt or now_sp()
    return dt.strftime("%H:%M:%S")


def header_block(roulette_name: str, date_str: str) -> str:
    return (
        "✅ Relatório ativo (janela deslizante)\n\n"
        f"🎰 ROLETA: {roulette_name}\n"
        f"📅 Data: {date_str}\n"
    )


def updated_time_block() -> str:
    return f"⏱ Atualizado: {fmt_time_br()} (UTC−3)\n"


def status_block(total_games: int, window_size: int) -> str:
    return (
        "\n\n"
        "📌 STATUS\n\n"
        f"• Quantidade de jogos (total): {total_games}\n\n"
        f"• Janela analisada: {window_size} (últimos {window_size})\n"
    )


def loading_block(progress_bar: str, count: int, window: int, percent: int) -> str:
    return (
        "\n\n"
        "📥 Carregando histórico para análise…\n"
        f"Progresso: {progress_bar} {count}/{window} ({percent}%)\n"
    )


def numbers_block(grid_text: str, total: int) -> str:
    return (
        "\n\n"
        f"🔢 ÚLTIMOS NÚMEROS ({total})\n\n"
        f"{grid_text}\n"
    )


def colors_block(grid_text: str, total: int) -> str:
    return (
        "\n\n"
        f"🎨 CORES ({total})\n\n"
        f"{grid_text}\n"
    )


def count_block(
    window: int,
    total_games: int,
    pares: int, pct_pares: int,
    impares: int, pct_impares: int,
    vermelhos: int, pct_vermelhos: int,
    pretos: int, pct_pretos: int,
    baixos: int, pct_baixos: int,
    altos: int, pct_altos: int,
) -> str:
    return (
        "\n\n"
        f"📌 CONTAGEM (janela {window} | total {total_games})\n\n"
        f"• Pares: {pares} ({pct_pares}%)\n\n"
        f"• Ímpares: {impares} ({pct_impares}%)\n\n\n"
        f"• Vermelhos: {vermelhos} ({pct_vermelhos}%) 🔴\n\n"
        f"• Pretos: {pretos} ({pct_pretos}%) ⚫\n\n\n"
        f"• Baixos (1–18): {baixos} ({pct_baixos}%) ⬇️\n\n"
        f"• Altos (19–36): {altos} ({pct_altos}%) ⬆️\n"
    )


def zeros_block(window: int, zeros: int, pct_zeros: int) -> str:
    return (
        "\n\n"
        f"📌 ZEROS (janela {window})\n\n"
        f"• Quantidade de ZEROS: {zeros} ({pct_zeros}%) 🟢\n"
    )


def _medal(i: int) -> str:
    return "🥇" if i == 0 else ("🥈" if i == 1 else "🥉")


def dominance_duzias_block(window: int, items: List[RankItem]) -> str:
    # items já vem ordenado
    lines = []
    for i, it in enumerate(items[:3]):
        if it.key == "1ª":
            label = "1ª Dúzia (1–12)"
        elif it.key == "2ª":
            label = "2ª Dúzia (13–24)"
        else:
            label = "3ª Dúzia (25–36)"
        lines.append(f"• {label}: {it.pct}% {_medal(i)}")
    return (
        "\n\n"
        f"📍 DOMINÂNCIA — DÚZIAS (janela {window} | ranking)\n\n"
        + "\n\n".join(lines)
        + "\n"
    )


def dominance_colunas_block(window: int, items: List[RankItem]) -> str:
    lines = []
    for i, it in enumerate(items[:3]):
        label = f"{it.key} Coluna"
        lines.append(f"• {label}: {it.pct}% {_medal(i)}")
    return (
        "\n\n"
        f"📍 DOMINÂNCIA — COLUNAS (janela {window} | ranking)\n\n"
        + "\n\n".join(lines)
        + "\n"
    )


def region_rank_block(window: int, items: List[RankItem]) -> str:
    lines = []
    for i, it in enumerate(items[:3]):
        lines.append(f"• {it.key}: {it.pct}% {_medal(i)}")
    return (
        "\n\n"
        f"📌 REGIÃO (janela {window} | ranking)\n\n"
        + "\n\n".join(lines)
        + "\n"
    )


def footer_block(total_games: int, last_number: Optional[int]) -> str:
    last_txt = "—" if last_number is None else str(last_number)
    return (
        "\n\n"
        "────────────────────\n"
        "📊 RESUMO FINAL\n\n"
        f"• Total de resultados acumulados: {total_games}\n\n"
        f"• Último número registrado: {last_txt}\n"
        "────────────────────\n"
    )
