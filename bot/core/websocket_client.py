# Cliente WebSocket (conexão + subscribe + reconexão + dedup)
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Awaitable

import pytz
import websockets


@dataclass
class WSConfig:
    ws_url: str
    casino_id: str
    currency: str
    table_key: int
    tz_name: str = "America/Sao_Paulo"


def build_subscribe_payload(casino_id: str, currency: str, table_key: int) -> Dict[str, Any]:
    return {
        "type": "subscribe",
        "casinoId": casino_id,
        "currency": currency,
        "key": [table_key],
    }


def _parse_pragmatic_time_to_sp(time_str: Any, tz_name: str) -> Optional[str]:
    """
    Pragmatic costuma mandar algo tipo: "Jan 12, 2026 02:33:12 PM"
    A gente converte pra SP e devolve string: "YYYY-MM-DD HH:MM:SS"
    """
    if time_str is None:
        return None

    s = str(time_str).strip()
    if not s:
        return None

    # formato do Pragmatic
    try:
        utc_naive = datetime.strptime(s, "%b %d, %Y %I:%M:%S %p")
        utc_dt = pytz.utc.localize(utc_naive)
        sp_tz = pytz.timezone(tz_name)
        sp_dt = utc_dt.astimezone(sp_tz)
        return sp_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # se não bater, só devolve o original mesmo (pra não quebrar tudo)
        return s


def _normalize_result(item: Dict[str, Any], tz_name: str) -> Optional[Dict[str, Any]]:
    """
    Normaliza um resultado pra ter sempre:
    - gameId (str)
    - result (str ou int em string)
    - time (YYYY-MM-DD HH:MM:SS) se possível
    """
    if not isinstance(item, dict):
        return None

    game_id = item.get("gameId")
    if game_id is None:
        return None

    result_val = item.get("result", item.get("number"))
    if result_val is None:
        return None

    norm: Dict[str, Any] = dict(item)  # mantém extras se vier
    norm["gameId"] = str(game_id).strip()
    norm["result"] = str(result_val).strip()
    norm["time"] = _parse_pragmatic_time_to_sp(item.get("time"), tz_name) or ""

    return norm


async def ws_run_forever(
    cfg: WSConfig,
    on_results: Callable[[List[Dict[str, Any]]], Awaitable[None]],
    should_run: Callable[[], bool],
    on_connection_change: Optional[Callable[[bool, Optional[str]], None]] = None,
) -> None:
    """
    Loop infinito:
    - conecta no WS
    - manda subscribe
    - recebe mensagens
    - extrai last20Results
    - normaliza
    - chama on_results(batch)

    should_run(): se retornar False, o loop finaliza.
    on_connection_change(connected, error_msg): callback opcional pra status.
    """
    backoff = 2.0
    backoff_max = 30.0

    while should_run():
        try:
            if on_connection_change:
                on_connection_change(False, None)

            async with websockets.connect(cfg.ws_url, ping_interval=20, ping_timeout=20) as websocket:
                # Conectou
                if on_connection_change:
                    on_connection_change(True, None)

                # Subscribe
                payload = build_subscribe_payload(cfg.casino_id, cfg.currency, cfg.table_key)
                await websocket.send(json.dumps(payload))

                backoff = 2.0  # reset backoff quando conecta com sucesso

                while should_run():
                    raw = await websocket.recv()
                    if not raw:
                        continue

                    try:
                        data = json.loads(raw)
                    except Exception:
                        continue

                    results = data.get("last20Results")
                    if not results:
                        continue
                    if not isinstance(results, list):
                        continue

                    batch: List[Dict[str, Any]] = []
                    for item in results:
                        norm = _normalize_result(item, cfg.tz_name)
                        if norm:
                            batch.append(norm)

                    if batch:
                        await on_results(batch)

        except asyncio.CancelledError:
            # encerramento limpo
            return

        except Exception as e:
            # caiu / erro / rede / ws fechou
            err = f"{type(e).__name__}: {e}"
            if on_connection_change:
                on_connection_change(False, err)

            # backoff antes de reconectar
            await asyncio.sleep(backoff)
            backoff = min(backoff * 1.6, backoff_max)

    # se should_run() ficou False, sai
    if on_connection_change:
        on_connection_change(False, "stopped")
