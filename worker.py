# worker.py
import asyncio
from logger import get_logger, setup_logging
from typing import Optional, Dict, Any, List

from dbhandler import PostgresRepository

setup_logging()
log = get_logger("worker")


class MessageProcessor:
    """
    Asynchrónny konzument meracích správ.
    - Fast-ACK zostáva vo websocket handleri.
    - Sem príde už rozparsovaný JSON (dict).
    - Ukladá ploché stĺpce + idempotentne dopĺňa RTT.
    """

    def __init__(self, repo: PostgresRepository, queue_maxsize: int = 10000) -> None:
        self.repo = repo
        self.queue: asyncio.Queue[Dict[str, Any]
                                  ] = asyncio.Queue(maxsize=queue_maxsize)
        self._task: Optional[asyncio.Task] = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(
            self._run(), name="measurement-worker")

    async def stop(self, drain: bool = True) -> None:
        # signal na zastavenie; voliteľne vyprázdnime queue
        self._stopping.set()
        if drain:
            await self.queue.join()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def enqueue(self, data: Dict[str, Any]) -> None:
        """Pridaj rozparsovanú správu do fronty. Ak je plná, čakaj (backpressure)."""
        try:
            self.queue.put_nowait(data)
        except asyncio.QueueFull:
            log.info("worker queue full; waiting to enqueue")
            await self.queue.put(data)

    async def _run(self) -> None:
        while True:
            log.info("worker waiting for data")
            data = await self.queue.get()
            try:
                typ = (data.get("type") or "").lower()

                if typ == "measurement":
                    mid = data.get("id")
                    if not mid:
                        log.info("measurement without id, skipping")
                        continue

                    # 1) insert measurement (ploché polia), idempotentne
                    try:
                        await self.repo.insert_measurement_flat(data)
                    except Exception:
                        log.exception(
                            "insert_measurement_flat failed for id=%s", mid)

                    # 2) rtt_updates priložené v measurement-e (voliteľné)
                    updates = data.get("rtt_updates") or []
                    if updates:
                        for upd in updates:
                            uid = upd.get("id")
                            rtt = upd.get("rtt_ms")
                            if uid is None or rtt is None:
                                continue
                            try:
                                await self.repo.apply_rtt(str(uid), float(rtt))
                            except Exception:
                                log.exception(
                                    "apply_rtt failed for id=%s (from carrier=%s)", uid, mid)

                elif typ == "rtt_updates":
                    # flush rámec z klienta: {"type":"rtt_updates","items":[{"id":"...","rtt_ms":...}, ...]}
                    items = data.get("items") or []
                    if not isinstance(items, list):
                        log.info("rtt_updates has no list 'items'; ignoring")
                    else:
                        applied = 0
                        for upd in items:
                            uid = upd.get("id")
                            rtt = upd.get("rtt_ms")
                            if uid is None or rtt is None:
                                continue
                            try:
                                await self.repo.apply_rtt(str(uid), float(rtt))
                                applied += 1
                            except Exception:
                                log.exception(
                                    "apply_rtt failed for id=%s (flush)", uid)
                        log.info("rtt_updates applied=%d", applied)

                else:
                    # probe alebo neznáme typy
                    log.info("ignoring message type=%s", typ or "<none>")

            except Exception:
                log.exception("worker failed on unexpected error")
            finally:
                log.info("worker task done")
                self.queue.task_done()
