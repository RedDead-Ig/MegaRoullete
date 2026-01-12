# Responsável por criar/editar a mensagem fixa (sem spam)
# Vai ter throttle e cache do último texto enviado
from __future__ import annotations

from typing import Optional

from telegram import Bot, Message
from telegram.error import BadRequest, TelegramError

from bot.storage.state import BotState


async def send_fixed_message(bot: Bot, state: BotState, chat_id: int, text: str) -> Message:
    """
    Envia a primeira mensagem (a que vai ficar sendo editada).
    Salva chat_id e message_id no state.
    """
    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        disable_web_page_preview=True,
    )
    state.set_fixed_message(chat_id=chat_id, message_id=msg.message_id)
    state.mark_edited(text)
    return msg


async def ensure_fixed_message(bot: Bot, state: BotState, chat_id: int, text: str) -> None:
    """
    Garante que existe uma mensagem fixa pra editar.
    Se ainda não existe, cria.
    """
    if state.chat_id is None or state.message_id is None:
        await send_fixed_message(bot, state, chat_id, text)
        return

    # Se o bot já tem uma message_id, mas chat_id mudou (ex: você iniciou em outro chat),
    # a gente "reancora" no chat atual criando uma nova mensagem fixa.
    if state.chat_id != chat_id:
        await send_fixed_message(bot, state, chat_id, text)


async def edit_fixed_message(
    bot: Bot,
    state: BotState,
    text: str,
    min_seconds_between_edits: float = 0.8,
    force: bool = False,
) -> bool:
    """
    Edita a mensagem fixa (sem spam).
    Retorna True se editou, False se não editou.
    """
    if state.chat_id is None or state.message_id is None:
        return False

    # Se o texto é igual ao último, não faz nada (evita "message is not modified")
    if text == state.last_render_text:
        return False

    # Rate limit: evita flood de edits
    if not force and not state.can_edit_now(min_seconds_between_edits):
        return False

    try:
        await bot.edit_message_text(
            chat_id=state.chat_id,
            message_id=state.message_id,
            text=text,
            disable_web_page_preview=True,
        )
        state.mark_edited(text)
        return True

    except BadRequest as e:
        # "Message is not modified" pode acontecer mesmo com cache (às vezes espaços etc.)
        msg = str(e).lower()

        if "message is not modified" in msg:
            state.mark_edited(text)
            return False

        # Se a mensagem não existe mais (apagaram), recria
        if "message to edit not found" in msg or "message identifier is not specified" in msg:
            new_msg = await bot.send_message(
                chat_id=state.chat_id,
                text=text,
                disable_web_page_preview=True,
            )
            state.set_fixed_message(chat_id=state.chat_id, message_id=new_msg.message_id)
            state.mark_edited(text)
            return True

        # Outras BadRequest: repassa
        raise

    except TelegramError:
        # Erros gerais (rede, timeout, etc.)
        return False


async def send_ephemeral(bot: Bot, chat_id: int, text: str) -> None:
    """
    Envia uma mensagem "normal" (não é a fixa).
    Útil pra /help, avisos, etc.
    """
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        disable_web_page_preview=True,
    )
