import asyncio
import websockets
import json
import time
import logging
import random

logging.basicConfig(level=logging.INFO)

async def send_data(websocket, path):
    while True:
        # Generate sample data
        data = {
            "timestamp": time.time(),
            "value": random.randint(1,100)  # Example value
        }
        await websocket.send(json.dumps(data))
        await asyncio.sleep(1)  # Send data every second

start_server = websockets.serve(send_data, '127.0.0.1', 1627)

logging.info("Starting WebSocket server on ws://0.0.0.0:1627")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()