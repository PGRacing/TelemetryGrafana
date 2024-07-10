import redis
import struct
import time
from pathlib import Path
import sys
from multiprocessing import Process, Queue

directory = Path(__file__).absolute()
 
# setting path
sys.path.append(f'{directory.parent.parent}')

from func_imu import gyro_data_live
from data_filtration import *

class Redis:
    def __init__(self, queue):
        self.redis_process = Process(target=self.start_redis_test, args=(queue,))
        self.redis_process.start()

    def start_redis(self, queue):
        self.r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        print('Starting redis.')

        gyro_data = GYROKalman()

        while True:
            id = queue.get()
            
            timestamp_bytes = bytearray()
            for i in range(6):
                timestamp_bytes.extend([queue.get()])
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
                        data_bytes.extend([queue.get()])
                    data = struct.unpack('>H', data_bytes)[0]

                    data_dict = {'counter':data}
                        
                    self.send_data_to_redis(time.time()*1000, data_dict)

                case 507:
                    gyro_data = gyro_data_live(queue, gyro_data)




            # wait for the next message
            # if 255 (0xff) is received, it means that the message is complete
            # else, the message is not complete and it's skipped
            while queue.get() != 255:
                pass

    def start_redis_test(self, queue):
        self.r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        print('Starting redis.')

        while True:
            value = queue.get()

            data_dict = {'counter': value,
                         'counter2': value/2,}
            self.send_data_to_redis(time.time()*1000, data_dict)
            print(f'Data sent to redis. counter: {value}')



    def send_data_to_redis(self, timestamp, data):
        for key, value in data.items():
            self.r.xadd(key, fields={'timestamp': timestamp, 'value': value})