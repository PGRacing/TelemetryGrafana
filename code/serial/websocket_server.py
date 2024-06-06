import asyncio
import functools
import websockets
import json
import logging
import serial
import struct
from multiprocessing import Process, Queue

logging.basicConfig(level=logging.INFO)

serial_com_port = "COM5"
serial_baudrate = 57600

def receive_data(queue):
    logging.info("Starting data reception on serial port.")
    ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate, timeout=0.02)
    while True:
        line = ser.read(1024)
        for byte in line:
            queue.put(byte)


async def send_data(websocket, path, async_queue):
    logging.info("send_data coroutine started.")
    while True:
        id = await async_queue.get()
        timestamp_bytes = bytearray()
        for i in range(6):
            timestamp_bytes.extend([await async_queue.get()])
        for i in range(2):
            timestamp_bytes.extend(b'\x00')
        timestamp = struct.unpack('<q', timestamp_bytes)[0]

        data_bytes = bytearray()
        for i in range (2):
            data_bytes.extend([await async_queue.get()])
        data = struct.unpack('>H', data_bytes)[0]

        ff = await async_queue.get()

        print(timestamp/1000)

        data = {
            "timestamp": timestamp,
            "value": data
        }
        await websocket.send(json.dumps(data))
        await asyncio.sleep(0.0001)

async def websocket_handler(websocket, path, async_queue):
    logging.info(f"New connection from {websocket.remote_address}")
    await send_data(websocket, path, async_queue)

async def websocket_start(async_queue):
    logging.info("Starting WebSocket server on ws://0.0.0.0:1627")
    server = await websockets.serve(functools.partial(websocket_handler, async_queue=async_queue), '127.0.0.1', 1627)
    logging.info("WebSocket server started.")
    await server.wait_closed()

def start_websocket_server(mp_queue):
    async_queue = asyncio.Queue()

    async def queue_forwarder():
        logging.info("Starting queue forwarder.")
        while True:
            item = await asyncio.get_event_loop().run_in_executor(None, mp_queue.get)
            await async_queue.put(item)

    async def main():
        asyncio.create_task(queue_forwarder())
        await websocket_start(async_queue)

    asyncio.run(main())

if __name__ == "__main__":
    mp_queue = Queue()
    receive_process = Process(target=receive_data, args=(mp_queue,))
    websocket_process = Process(target=start_websocket_server, args=(mp_queue,))

    receive_process.start()
    websocket_process.start()

    receive_process.join()
    websocket_process.join()
