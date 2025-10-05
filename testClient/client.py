# ws_client.py
import asyncio
import json
import time
import uuid
from collections import deque
import websockets
import secrets
import time

URL = "ws://127.0.0.1:8000/ws"
MAX_RTT_UPDATES = 20


def make_measurement(mid: str, rtt_updates):
    return {
        "type": "measurement",
        "id": mid,
        "timestamp_sent": int(time.time() * 1000),
        "radio": {"rsrp": -900, "rsrq": -10, "sinr": 20, "cell_id": 123456, "network_type": "5G"},
        "position": {"lat": 48.456, "lon": 17.065, "speed_kmh": 95.2},
        "device": {"operator": "O2", "device_id": "TEST_" + uuid.uuid4().hex[:8]},
        "v2x": {"kind": "BSM", "payload": {"speed_kmh": 95.2, "heading_deg": 182.4}},
        "rtt_updates": list(rtt_updates)[-MAX_RTT_UPDATES:]
    }


def make_id():
    ms = int(time.time() * 1000)
    suf = secrets.token_hex(4)
    return f"{ms}-{suf}"


async def main():

    async with websockets.connect(URL, compression=None) as ws:
        rtt_outbox = deque()
        for i in range(5):
            mid = make_id()
            payload = make_measurement(mid, rtt_outbox)

            t0 = time.monotonic_ns()
            await ws.send(json.dumps(payload, separators=(',', ':')))
            raw = await ws.recv()
            t1 = time.monotonic_ns()

            rtt_ms = (t1 - t0) / 1e6
            print(raw, f"RTT≈{rtt_ms:.2f} ms")

            rtt_outbox.append({"id": mid, "rtt_ms": rtt_ms})

            while len(rtt_outbox) > 100:
                rtt_outbox.popleft()

            await asyncio.sleep(0.4)

if __name__ == "__main__":
    asyncio.run(main())
