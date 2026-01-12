# Aqui entram os handlers do Telegram:
# /start, /stop, /status, /configurar_janela, /help
from __future__ import annotations

from typing import List, Optional

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.config import (
    DEFAULT_WINDOW_SIZE,
    MIN_SECONDS_BETWEEN_EDITS,
    is_admin,
    validate_window_size,
)
from bot.storage.state import BotState
from bot.telegram.messenger import ensure_fixed_message, edit_fixed_message, send_ephemeral
from bot.telegram import texts


ROULETTE_NAME = "Mega Roulette Multiplicadora"


def _get_state(context: ContextTypes.DEFAULT_TYPE) -> BotState:
    """
    Guarda o estado dentro do application.bot_data
    (assim todos os handlers e tarefas compartilham o mesmo estado).
    """
    app = context.application
    if "state" not in app.bot_data:
        app.bot_data["state"] = BotState(window_size=DEFAULT_WINDOW_SIZE)
    return app.bot_data["state"]


def _render_placeholder_message(state: BotState) -> str:
    """
    Mensagem padrão enquanto ainda não temos os dados conectados/rodando.
    (Depois, o formatter vai substituir isso com números/cores e contagens reais.)
    """
    date_str = texts.fmt_date_br()
    title = texts.running_title_block(window=state.window_size, ready=(len(state.results) >= state.window_size))
    progress = texts.loading_block(
        progress_bar=state.progress_bar(20),
        count=state.progress_count(),
        window=state.window_size,
        percent=state.progress_percent(),
    )

    body = (
        "\n\n"
        "🔢 ÚLTIMOS NÚMEROS\n\n"
        "Aguardando dados...\n"
        "\n\n"
        "🎨 CORES\n\n"
        "Aguardando dados...\n"
    )

    # contagem placeholder (0 enquanto não tem analytics ligado)
    counts = texts.count_block(
        window=state.progress_count() if len(state.results) < state.window_size else state.window_size,
        pares=0,
        impares=0,
        zeros=0,
        vermelhos=0,
        pretos=0,
        verdes=0,
        baixos=0,
        altos=0,
    )

    dom = texts.dominance_block(
        window=state.progress_count() if len(state.results) < state.window_size else state.window_size,
        duzia="—",
        coluna="—",
    )

    return texts.header_block(ROULETTE_NAME, date_str) + "\n\n" + title + progress + body + counts + dom


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    chat_id = chat.id
    if not is_admin(chat_id):
        # silencioso (pra não dar palco)
        return

    state = _get_state(context)
    state.running = True
    state.ws_last_error = None

    text = _render_placeholder_message(state)
    await ensure_fixed_message(context.bot, state, chat_id, text)

    # confirma sem spam: manda uma mensagem curta (opcional)
    await send_ephemeral(context.bot, chat_id, "✅ Bot ligado. Vou atualizar o relatório nessa mensagem fixa.")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    chat_id = chat.id
    if not is_admin(chat_id):
        return

    state = _get_state(context)
    state.running = False

    text = (
        "⏸️ Bot pausado\n\n"
        f"🎰 ROLETA: {ROULETTE_NAME}\n"
        f"📅 Data: {texts.fmt_date_br()}\n\n"
        "Use /start pra voltar.\n"
    )

    # se já existir mensagem fixa, edita. se não, manda normal.
    edited = await edit_fixed_message(
        context.bot,
        state,
        text,
        min_seconds_between_edits=MIN_SECONDS_BETWEEN_EDITS,
        force=True,
    )
    if not edited:
        await send_ephemeral(context.bot, chat_id, text)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    chat_id = chat.id
    if not is_admin(chat_id):
        return

    state = _get_state(context)

    status = "ON ✅" if state.running else "OFF ⏸️"
    ws = "conectado ✅" if state.ws_connected else "desconectado ⚠️"
    msg = (
        "📈 STATUS\n\n"
        f"• Bot: {status}\n\n"
        f"• WS: {ws}\n\n"
        f"• Janela: {state.window_size}\n\n"
        f"• Progresso: {state.progress_count()}/{state.window_size} ({state.progress_percent()}%)\n"
    )

    if state.ws_last_error:
        msg += f"\n• Último erro: {state.ws_last_error}\n"

    await send_ephemeral(context.bot, chat_id, msg)


async def cmd_configurar_janela(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    chat_id = chat.id
    if not is_admin(chat_id):
        return

    state = _get_state(context)

    # /configurar_janela 80
    args = context.args or []
    if not args:
        await send_ephemeral(
            context.bot,
            chat_id,
            "⚙️ Use assim:\n\n/configurar_janela 40\n\nValores típicos: 20, 40, 60, 80, 100",
        )
        return

    raw = args[0].strip()
    try:
        n = int(raw)
    except ValueError:
        await send_ephemeral(context.bot, chat_id, "❌ Isso não é número. Ex: /configurar_janela 80")
        return

    n = validate_window_size(n)
    state.set_window_size(n)

    # Atualiza a mensagem fixa imediatamente com placeholder (por enquanto)
    text = _render_placeholder_message(state)
    await ensure_fixed_message(context.bot, state, chat_id, text)
    await edit_fixed_message(
        context.bot,
        state,
        text,
        min_seconds_between_edits=MIN_SECONDS_BETWEEN_EDITS,
        force=True,
    )

    await send_ephemeral(context.bot, chat_id, f"✅ Janela atualizada para {n}. Agora vou trabalhar com os últimos {n}.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    chat_id = chat.id
    if not is_admin(chat_id):
        return

    msg = (
        "🧾 COMANDOS\n\n"
        "/start - inicia o robô\n\n"
        "/stop - pausa o robô\n\n"
        "/status - mostra status\n\n"
        "/configurar_janela N - define janela (ex: 40, 80, 100)\n\n"
        "/id - mostra seu chat_id\n"
    )
    await send_ephemeral(context.bot, chat_id, msg)


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    await send_ephemeral(context.bot, chat.id, f"🆔 chat_id: {chat.id}")


def build_handlers() -> List[CommandHandler]:
    """
    Retorna a lista de handlers pra main.py registrar.
    """
    return [
        CommandHandler("start", cmd_start),
        CommandHandler("stop", cmd_stop),
        CommandHandler("status", cmd_status),
        CommandHandler("configurar_janela", cmd_configurar_janela),
        CommandHandler("help", cmd_help),
        CommandHandler("id", cmd_id),
    ]
