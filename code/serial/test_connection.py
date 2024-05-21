import asyncio
import websockets
import logging

logging.basicConfig(level=logging.INFO)

async def receive_data():
    uri = "ws://127.0.0.1:1627"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(data)

asyncio.get_event_loop().run_until_complete(receive_data())
