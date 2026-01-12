from __future__ import annotations

from datetime import datetime
from typing import List, Optional

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
    # fica claro no mobile que é fuso BR
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
    # detalhe: o cabeçalho (janela | total) vai PRA BAIXO em uma linha separada
    return (
        "\n\n"
        "📌 CONTAGEM\n\n"
        f"(janela {window} | total {total_games})\n\n"
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
        "📌 ZEROS\n\n"
        f"(janela {window})\n\n"
        f"• Quantidade de ZEROS: {zeros} ({pct_zeros}%) 🟢\n"
    )


def _medal(i: int) -> str:
    # medalha só pros 3 primeiros
    if i == 0:
        return "🥇"
    if i == 1:
        return "🥈"
    if i == 2:
        return "🥉"
    return ""


def dominance_duzias_block(window: int, items: List[RankItem]) -> str:
    # items já vem ordenado (maior % -> menor %)
    lines: List[str] = []
    for i, it in enumerate(items[:3]):
        if it.key == "1ª":
            label = "1ª Dúzia (1–12)"
        elif it.key == "2ª":
            label = "2ª Dúzia (13–24)"
        else:
            label = "3ª Dúzia (25–36)"

        medal = _medal(i)
        suffix = f" {medal}" if medal else ""
        lines.append(f"• {label}: {it.pct}%{suffix}")

    return (
        "\n\n"
        "📍 DOMINÂNCIA — DÚZIAS\n\n"
        f"(janela {window} | ranking)\n\n"
        + "\n\n".join(lines)
        + "\n"
    )


def dominance_colunas_block(window: int, items: List[RankItem]) -> str:
    lines: List[str] = []
    for i, it in enumerate(items[:3]):
        label = f"{it.key} Coluna"
        medal = _medal(i)
        suffix = f" {medal}" if medal else ""
        lines.append(f"• {label}: {it.pct}%{suffix}")

    return (
        "\n\n"
        "📍 DOMINÂNCIA — COLUNAS\n\n"
        f"(janela {window} | ranking)\n\n"
        + "\n\n".join(lines)
        + "\n"
    )


def region_rank_block(window: int, items: List[RankItem]) -> str:
    # Agora imprime 4 regiões (se vier 4)
    lines: List[str] = []
    for i, it in enumerate(items[:4]):
        medal = _medal(i)
        suffix = f" {medal}" if medal else ""
        lines.append(f"• {it.key}: {it.pct}%{suffix}")

    return (
        "\n\n"
        "📌 REGIÃO\n\n"
        f"(janela {window} | ranking)\n\n"
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
