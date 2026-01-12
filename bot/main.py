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
from bot.telegram.messenger import edit_fixed_message


def _get_state(app: Application) -> BotState:
    if "state" not in app.bot_data:
        app.bot_data["state"] = BotState()
    return app.bot_data["state"]


async def _post_init(app: Application) -> None:
    """Roda quando o app inicia. Aqui a gente sobe o WebSocket em background."""
    state = _get_state(app)

    ws_cfg = WSConfig(
        ws_url=ROULETTE_WS_URL,
        casino_id=CASINO_ID,
        currency=CURRENCY,
        table_key=TABLE_KEY,
    )

    async def on_results(batch):
        # só processa se o bot estiver ligado via /start
        if not state.running:
            return

        added = add_results(state, batch)
        if added <= 0:
            return

        text = render_report(state)

        await edit_fixed_message(
            bot=app.bot,
            state=state,
            text=text,
            min_seconds_between_edits=MIN_SECONDS_BETWEEN_EDITS,
            force=False,
        )

    def should_run_ws() -> bool:
        # o cancel do task cuida de parar
        return True

    def on_connection_change(connected: bool, error_msg: str | None):
        state.ws_connected = connected
        state.ws_last_error = error_msg

    async def ws_task():
        await ws_run_forever(
            cfg=ws_cfg,
            on_results=on_results,
            should_run=should_run_ws,
            on_connection_change=on_connection_change,
        )

    # cria task dentro do loop do PTB
    app.bot_data["ws_task"] = app.create_task(ws_task(), name="ws_task")


async def _post_shutdown(app: Application) -> None:
    """Roda quando o app vai desligar. Cancela o WebSocket bonitinho."""
    task = app.bot_data.get("ws_task")
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass


def run() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Faltou TELEGRAM_BOT_TOKEN nas variáveis de ambiente.")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    for h in build_handlers():
        app.add_handler(h)

    # run_polling já cuida de init/start/idle/shutdown do jeito certo
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run()
