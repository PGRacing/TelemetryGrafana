import asyncio
import websockets

async def test_connection():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        print(await websocket.recv())

asyncio.get_event_loop().run_until_complete(test_connection())
