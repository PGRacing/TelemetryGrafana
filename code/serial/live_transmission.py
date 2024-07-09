import logging
import serial
import struct
import redis
from Redis import Redis
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

# def start_redis(queue):
#     r = redis.Redis(host='127.0.0.1', port=6379, db=0)
#     logging.info("Starting redis.")

#     while True:
#         id = queue.get()
        
#         timestamp_bytes = bytearray()
#         for i in range(6):
#             timestamp_bytes.extend([queue.get()])
#         fulfilling to 8 bytes
#         for i in range(2):
#             timestamp_bytes.extend(b'\x00')

#         timestamp must be in milliseconds since epoch
#         receiverd timestamp is already in milliseconds
#         timestamp = struct.unpack('<q', timestamp_bytes)[0]

#         match id:
#             test case (counter)
#             case 5:
#                 data_bytes = bytearray()
#                 for i in range (2):
#                     data_bytes.extend([queue.get()])
#                 data = struct.unpack('>H', data_bytes)[0]

#                 data_dict = {"counter":data}
                      
#                 send_data_to_redis(timestamp, data_dict, r)

#             gyro frame
#             case 507:
#                 data_bytes = bytearray()
#                 for i in range (6):
#                     data_bytes.extend([queue.get()])
#                 acc_x, acc_y, acc_z = struct.upack("<HHH", data)[0]
#                 acc_x /= 128.
#                 acc_y /= 128.
#                 acc_z /= 128.

#                 data = {
#                     "timestamp": timestamp,
#                     "value": acc_x
#                 }
#                 data = {
#                     "timestamp": timestamp,
#                     "value": acc_y
#                 }
#                 data = {
#                     "timestamp": timestamp,
#                     "value": acc_z
#                 }

#                 r.xadd('acc_x', fields=data)
#                 r.xadd('acc_y', fields=data)
#                 r.xadd('acc_z', fields=data)

#         wait for the next message
#         if 255 (0xff) is received, it means that the message is complete
#         else, the message is not complete and it's skipped
#         while queue.get() != 255:
#             pass


# def send_data_to_redis(timestamp, data, r):
#     for key, value in data.items():
#         r.xadd(key, fields={"timestamp": timestamp, "value": value})


if __name__ == "__main__":
    queue = Queue()
    r = Redis()

    receive_process = Process(target=receive_data, args=(queue,))
    websocket_process = Process(target=r.start_redis, args=(queue,))

    receive_process.start()
    websocket_process.start()

    receive_process.join()
    websocket_process.join()