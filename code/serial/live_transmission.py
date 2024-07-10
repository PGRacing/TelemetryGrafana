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
    


if __name__ == "__main__":
    queue = Queue()

    send_process = Process(target=send_data, args=(queue,))
   # receive_process = Process(target=receive_data, args=(queue,))
    r = Redis(queue)

  #  receive_process.start()
    send_process.start()

