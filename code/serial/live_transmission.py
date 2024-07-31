import logging
import serial
import time
from Redis import *
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
def send_data(queue):
    counter = 1
    logging.info("Starting data to queue.")
    while True:
        queue.put(counter)
        counter += 1
        time.sleep(0.01)

def start_redis_process(queue):
    redis_instance = Redis()
    redis_instance.start_redis(queue)

def start_websocket_server(queue_to_websocket):
    redis_instance = Redis()
    websocket_url = 'ws://127.0.0.1:1627'
    start_server = websockets.serve(redis_instance.websocket_handler, '127.0.0.1', 1627)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    


if __name__ == "__main__":
    queue = Queue()

  #  send_process = Process(target=send_data, args=(queue_from_serial,))
    receive_process = Process(target=receive_data, args=(queue,))
   # redis_process = Process(target=start_redis_process, args=(queue_from_serial,))
   # websocket_process = Process(target=start_websocket_server, args=(queue_to_websocket,))

    r = Redis(queue)

    receive_process.start()
  #  send_process.start()
 #   redis_process.start()
   # websocket_process.start()

