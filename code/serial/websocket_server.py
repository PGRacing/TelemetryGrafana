import asyncio
import websockets
import json
import time
import logging
import random
import serial
import struct
import datetime

logging.basicConfig(level=logging.INFO)

serial_com_port = "COM5"
serial_baudrate=57600

ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate, timeout=0.02)

async def send_data(websocket, path):
    while True:
        line = ser.read(1024)

        if(len(line)>8 and line[0] == 0x05):
            id = line[0]
            timestamp_bytes = bytearray(line[1:7])
            for i in range(2):
                timestamp_bytes.extend(b'\x00')
            timestamp = struct.unpack('<q', timestamp_bytes)[0]
            data = struct.unpack('>H', line[7:9])[0]

        # sample data
            data = {
                "timestamp": timestamp, # time must be snt as float (seconds)
                "value": data
            }
            await websocket.send(json.dumps(data))
            await asyncio.sleep(0.0001)  # send data every second

start_server = websockets.serve(send_data, '127.0.0.1', 1627)

logging.info("Starting WebSocket server on ws://0.0.0.0:1627")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()