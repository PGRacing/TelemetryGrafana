import asyncio
import functools
import websockets
import json
import logging
import serial
import struct
import redis
from multiprocessing import Process, Queue
from concurrent.futures import ThreadPoolExecutor
from time import sleep, time
from redistimeseries.client import Client

executor = ThreadPoolExecutor()

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
    logging.info("send_data() started.")
    loop = asyncio.get_event_loop()
    rts = Client()
    rts.create('telemetry_data', retention_msecs=7200000, labels={'time': 'series'})
 #   pool = init_redis()

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

        data = {
            "timestamp": timestamp,
            "value": data
        }



async def start_redis(async_queue):
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    logging.info("Starting redis.")

    counter = 1
    while True:
      #  counter= counter + 1
      #  r.set('foo', counter)
      #  r.set('acc', 2)


       # sleep(0.1)

       # sample = {
       #     "timestamp": time() *1000,
       #     "value": counter
       # }

       # r.xadd('data', fields=sample)


        #------------------------


        id = await async_queue.get()
        
        timestamp_bytes = bytearray()
        for i in range(6):
            timestamp_bytes.extend([await async_queue.get()])
        # fulfilling to 8 bytes
        for i in range(2):
            timestamp_bytes.extend(b'\x00')

        # timestamp must be in milliseconds since epoch
        # receiverd timestamp is already in milliseconds
        timestamp = struct.unpack('<q', timestamp_bytes)[0]

        match id:
            # test case (counter)
            case 5:
                data_bytes = bytearray()
                for i in range (2):
                    data_bytes.extend([await async_queue.get()])
                data = struct.unpack('>H', data_bytes)[0]

                data = {
                    "timestamp": timestamp,
                    "value": data
                }

                r.xadd('counter', fields=data)

            # gyro frame
            case 507:
                data_bytes = bytearray()
                for i in range (6):
                    data_bytes.extend([await async_queue.get()])
                acc_x, acc_y, acc_z = struct.upack("<HHH", data)[0]
                acc_x /= 128.
                acc_y /= 128.
                acc_z /= 128.

                data = {
                    "timestamp": timestamp,
                    "value": acc_x
                }
                data = {
                    "timestamp": timestamp,
                    "value": acc_y
                }
                data = {
                    "timestamp": timestamp,
                    "value": acc_z
                }

                r.xadd('acc_x', fields=data)
                r.xadd('acc_y', fields=data)
                r.xadd('acc_z', fields=data)

        # wait for the next message
        # if 255 (0xff) is received, it means that the message is complete
        # else, the message is not complete and it's skipped
        while await async_queue.get() != 255:
            pass





def copy_multiprocessing_queue_to_asyc(mp_queue):
    async_queue = asyncio.Queue()

    async def queue_forwarder():
        logging.info("Starting queue forwarder.")
        while True:
            item = await asyncio.get_event_loop().run_in_executor(None, mp_queue.get)
            await async_queue.put(item)

    async def main():
        asyncio.create_task(queue_forwarder())
        await start_redis(async_queue)

    asyncio.run(main())


if __name__ == "__main__":
    mp_queue = Queue()

    receive_process = Process(target=receive_data, args=(mp_queue,))
    websocket_process = Process(target=copy_multiprocessing_queue_to_asyc, args=(mp_queue,))

    receive_process.start()
    websocket_process.start()

    receive_process.join()
    websocket_process.join()