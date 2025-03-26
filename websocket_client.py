import asyncio
import threading
import websockets
import json

class BinanceWS:
    def __init__(self):
        # Tüm coinler için güncel fiyatları saklayan sözlük
        self.latest_prices = {}
        self._start_ws_thread()

    async def _listen(self):
        # Combined stream URL: tüm coinlerin stream isimleri tamamen küçük harflerle olmalı.
        uri = ("wss://fstream.binance.com/stream?streams="
               "btcusdt@markPrice/ethusdt@markPrice/bnbusdt@markPrice/"
               "solusdt@markPrice/xrpusdt@markPrice")
        async with websockets.connect(uri) as ws:
            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)
                    # Combined stream mesajları: {"stream": "<streamName>", "data": { ... }}
                    if "data" in data:
                        data = data["data"]
                    if "s" in data and "p" in data:
                        self.latest_prices[data["s"]] = data["p"]
                        print(f"Received {data['s']} price: {data['p']}")
                except Exception as e:
                    print("WebSocket error:", e)
                    break

    def _start_ws_thread(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        asyncio.run(self._listen())

def get_binance_ws():
    return BinanceWS()
