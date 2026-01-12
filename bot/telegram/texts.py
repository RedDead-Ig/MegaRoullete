# Templates de mensagem (o textão bonitão com espaçamento)
from __future__ import annotations

from datetime import datetime
from typing import Optional


def fmt_date_br(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.now()
    return dt.strftime("%d/%m/%Y")


def fmt_time_br(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.now()
    return dt.strftime("%H:%M:%S")


def header_block(roulette_name: str, date_str: str) -> str:
    return (
        "🤖 Robô de análise iniciado\n\n"
        f"🎰 ROLETA: {roulette_name}\n"
        f"📅 Data: {date_str}\n"
    )


def loading_block(progress_bar: str, count: int, window: int, percent: int) -> str:
    return (
        "\n\n"
        "📥 Carregando histórico para análise…\n"
        f"Progresso: {progress_bar} {count}/{window} ({percent}%)\n"
    )


def numbers_block(title: str, grid_text: str, total: int) -> str:
    return (
        "\n\n"
        f"🔢 {title} ({total})\n\n"
        f"{grid_text}\n"
    )


def colors_block(title: str, grid_text: str, total: int) -> str:
    return (
        "\n\n"
        f"🎨 {title} ({total})\n\n"
        f"{grid_text}\n"
    )


def count_block(
    window: int,
    pares: int,
    impares: int,
    zeros: int,
    vermelhos: int,
    pretos: int,
    verdes: int,
    baixos: int,
    altos: int,
) -> str:
    # Espaçamento EXATO do jeito que você pediu (linha em branco entre itens)
    return (
        "\n\n"
        f"📌 CONTAGEM ({window})\n\n"
        f"• Pares: {pares}\n\n"
        f"• Ímpares: {impares}\n\n"
        f"• Zero: {zeros} 🟢\n\n\n"
        f"• Vermelhos: {vermelhos} 🔴\n\n"
        f"• Pretos: {pretos} ⚫\n\n"
        f"• Verdes: {verdes} 🟢\n\n\n"
        f"• Baixos (1–18): {baixos} ⬇️\n\n"
        f"• Altos (19–36): {altos} ⬆️\n"
    )


def dominance_block(window: int, duzia: str, coluna: str) -> str:
    return (
        "\n\n"
        f"📍 DOMINÂNCIA ({window})\n\n"
        f"• Dúzia predominante: {duzia}\n\n"
        f"• Coluna predominante: {coluna}\n"
    )


def running_title_block(window: int, ready: bool) -> str:
    if ready:
        return (
            "✅ Janela completa! Relatório ativo\n\n"
            f"📊 RELATÓRIO — Janela: Últimos {window}\n"
            f"⏱ Atualizado: {fmt_time_br()}\n"
        )
    return (
        "🤖 Robô de análise em execução\n\n"
        f"📊 PRÉ-RELATÓRIO — Montando janela: {window}\n"
        f"⏱ Atualizado: {fmt_time_br()}\n"
    )


def error_block(msg: str) -> str:
    return (
        "\n\n"
        "⚠️ ERRO / CONEXÃO\n\n"
        f"{msg}\n"
    )
