from __future__ import annotations

import asyncio

from telegram.ext import Application

from bot.config import (
    TELEGRAM_BOT_TOKEN,
    MIN_SECONDS_BETWEEN_EDITS,
    ROULETTE_WS_URL,
    CASINO_ID,
    CURRENCY,
    TABLE_KEY,
)
from bot.core.buffer import add_results
from bot.core.formatter import render_report
from bot.core.websocket_client import WSConfig, ws_run_forever
from bot.storage.state import BotState
from bot.telegram.handlers import build_handlers


def _get_state(app: Application) -> BotState:
    if "state" not in app.bot_data:
        app.bot_data["state"] = BotState()
    return app.bot_data["state"]


async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Faltou TELEGRAM_BOT_TOKEN nas variáveis de ambiente.")

    # Telegram app
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # registra comandos
    for h in build_handlers():
        app.add_handler(h)

    state = _get_state(app)

    # callback quando chegar batch do websocket
    async def on_results(batch):
        # só processa quando bot está rodando (evita editar parado)
        if not state.running:
            return

        # adiciona resultados na janela
        added = add_results(state, batch)
        if added <= 0:
            return

        # renderiza texto final
        text = render_report(state)

        # edita a mensagem fixa (se existir)
        # (Se ainda não teve /start, não tem message_id — então não faz nada)
        from bot.telegram.messenger import edit_fixed_message

        await edit_fixed_message(
            bot=app.bot,
            state=state,
            text=text,
            min_seconds_between_edits=MIN_SECONDS_BETWEEN_EDITS,
            force=False,
        )

    def should_run_ws() -> bool:
        # O WS roda sempre, mas o loop pode ser encerrado se o app for fechar.
        return True

    def on_connection_change(connected: bool, error_msg: str | None):
        state.ws_connected = connected
        state.ws_last_error = error_msg

    ws_cfg = WSConfig(
        ws_url=ROULETTE_WS_URL,
        casino_id=CASINO_ID,
        currency=CURRENCY,
        table_key=TABLE_KEY,
    )

    # task do websocket em background (dentro do mesmo event loop do telegram)
    async def start_ws_task():
        await ws_run_forever(
            cfg=ws_cfg,
            on_results=on_results,
            should_run=should_run_ws,
            on_connection_change=on_connection_change,
        )

    # Inicia e roda
    await app.initialize()
    await app.start()

    # cria a tarefa do WS
    ws_task = asyncio.create_task(start_ws_task(), name="ws_task")

    # start polling (não retorna até parar)
    try:
        await app.updater.start_polling(drop_pending_updates=True)
        await app.updater.idle()
    finally:
        ws_task.cancel()
        try:
            await ws_task
        except Exception:
            pass

        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
