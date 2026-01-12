from __future__ import annotations

from typing import List

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from bot.config import (
    DEFAULT_WINDOW_SIZE,
    MIN_SECONDS_BETWEEN_EDITS,
    is_admin,
    validate_window_size,
)
from bot.storage.state import BotState
from bot.telegram.messenger import ensure_fixed_message, edit_fixed_message, send_ephemeral
from bot.core.formatter import render_report


def _get_state(context: ContextTypes.DEFAULT_TYPE) -> BotState:
    app = context.application
    if "state" not in app.bot_data:
        app.bot_data["state"] = BotState(window_size=DEFAULT_WINDOW_SIZE)
    return app.bot_data["state"]


async def _refresh_fixed_message(context: ContextTypes.DEFAULT_TYPE, state: BotState, chat_id: int, force: bool = False) -> None:
    text = render_report(state)
    await ensure_fixed_message(context.bot, state, chat_id, text)
    await edit_fixed_message(
        context.bot,
        state,
        text,
        min_seconds_between_edits=MIN_SECONDS_BETWEEN_EDITS,
        force=force,
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id

    if not is_admin(chat_id):
        return

    state = _get_state(context)
    state.running = True
    state.awaiting_window_size = False
    state.awaiting_window_size_chat_id = None

    await _refresh_fixed_message(context, state, chat_id, force=True)
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
    state.awaiting_window_size = False
    state.awaiting_window_size_chat_id = None

    await send_ephemeral(context.bot, chat_id, "⏸️ Bot pausado. Use /start pra voltar.")


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
        f"• Total acumulado: {state.total_games}\n\n"
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

    args = context.args or []

    # Caso 1: veio número junto => aplica direto
    if args:
        raw = args[0].strip()
        try:
            n = int(raw)
        except ValueError:
            await send_ephemeral(context.bot, chat_id, "❌ Isso não é número. Ex: /configurar_janela 20")
            return

        n = validate_window_size(n)
        state.set_window_size(n)
        state.awaiting_window_size = False
        state.awaiting_window_size_chat_id = None

        await send_ephemeral(context.bot, chat_id, f"✅ Nova janela configurada com sucesso: {n}\n\n🔄 Recalibrando…")
        await _refresh_fixed_message(context, state, chat_id, force=True)
        return

    # Caso 2: sem args => entra em modo “aguardando”
    state.awaiting_window_size = True
    state.awaiting_window_size_chat_id = chat_id

    await send_ephemeral(
        context.bot,
        chat_id,
        "⚙️ Configurar Janela\n\n"
        "Envie agora o número da janela.\n\n"
        "Exemplos: 20, 40, 60, 80, 100",
    )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id

    if not is_admin(chat_id):
        return

    state = _get_state(context)

    # Só pega texto “solto” se estiver aguardando a janela
    if not state.awaiting_window_size:
        return

    if state.awaiting_window_size_chat_id is not None and state.awaiting_window_size_chat_id != chat_id:
        return

    text = (update.effective_message.text or "").strip()

    # Se o cara mandar qualquer coisa que não seja número, dá feedback
    try:
        n = int(text)
    except ValueError:
        await send_ephemeral(context.bot, chat_id, "❌ Manda só o número. Ex: 20")
        return

    n = validate_window_size(n)
    state.set_window_size(n)
    state.awaiting_window_size = False
    state.awaiting_window_size_chat_id = None

    await send_ephemeral(context.bot, chat_id, f"✅ Nova janela configurada com sucesso: {n}\n\n🔄 Recalibrando…")
    await _refresh_fixed_message(context, state, chat_id, force=True)


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
        "/status - status rápido\n\n"
        "/configurar_janela - escolhe janela (ex: /configurar_janela 20)\n\n"
        "Dica: se mandar só /configurar_janela, depois manda só o número (ex: 20)\n"
    )
    await send_ephemeral(context.bot, chat_id, msg)


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    await send_ephemeral(context.bot, chat.id, f"🆔 chat_id: {chat.id}")


def build_handlers() -> List:
    return [
        CommandHandler("start", cmd_start),
        CommandHandler("stop", cmd_stop),
        CommandHandler("status", cmd_status),
        CommandHandler("configurar_janela", cmd_configurar_janela),
        CommandHandler("help", cmd_help),
        CommandHandler("id", cmd_id),

        # pega “20” solto quando estiver em modo aguardando
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input),
    ]
