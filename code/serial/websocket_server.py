import asyncio
import websockets
import json
import time

async def send_data(websocket, path):
    while True:
        # Generate sample data
        data = {
            "timestamp": time.time(),
            "value": 42  # Example value
        }
        await websocket.send(json.dumps(data))
        await asyncio.sleep(1)  # Send data every second

start_server = websockets.serve(send_data, 'localhost', 8091)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
