# websocket.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from logger import get_logger, setup_logging
from worker import MessageProcessor

setup_logging()
log = get_logger("websocket")

router = APIRouter()


class WsController:
    def __init__(self, processor: MessageProcessor):
        self.processor = processor

    async def handle(self, ws: WebSocket):
        await ws.accept()
        peer = ws.client
        ua = ws.headers.get("user-agent", "-")
        log.info("WS connected from %s:%s ua=%s", getattr(
            peer, "host", "?"), getattr(peer, "port", "?"), ua)
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    data = json.loads(raw)
                except Exception:
                    # nevalidný JSON – neACK-uj, nenúť worker, len zaloguj
                    log.info("Invalid JSON (ignored)")
                    continue

                mid = data.get("id")
                if mid:
                    # fast-ACK hneď
                    await ws.send_text(json.dumps({"type": "measurement_ack", "id": mid}))
                    log.info("ACK sent id=%s", mid)

                # spracovanie mimo ACK cesty
                log.info("Enqueuing data")
                await self.processor.enqueue(data)
        except WebSocketDisconnect:
            pass
