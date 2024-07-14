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
from func_gps import gps_data_live
from lap_timer import LapTimer
from func_ecumaster import *
from data_filtration import *

class Redis:
    def __init__(self, queue):
        self.redis_process = Process(target=self.start_redis_test, args=(queue,))
        self.redis_process.start()

    def start_redis(self, queue):
        self.r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        print('Starting redis.')

        self.init_previous_values()
        self.init_filters()

        while True:
            id = hex(queue.get())
            
            timestamp_bytes = bytearray()
            for i in range(6):
                timestamp_bytes.extend([queue.get()])
            # fulfilling to 8 bytes
            for i in range(2):
                timestamp_bytes.extend(b'\x00')

            # timestamp must be in milliseconds since epoch
            # receiverd timestamp is already in milliseconds
            timestamp = struct.unpack('<q', timestamp_bytes)[0]

            self.match_id(id, timestamp, queue)

            # wait for the next message
            # if 255 (0xff) is received, it means that the message is complete
            # else, the message is not complete and it's skipped
            while queue.get() != 255:
                pass

    def match_id(self, id, timestamp, queue):
        frame_to_send = None

        match id:
            # test case (counter)
            case 5:
                data_bytes = bytearray()
                for i in range (2):
                    data_bytes.extend([queue.get()])
                data = struct.unpack('>H', data_bytes)[0]

                data_dict = {'counter':data}
                    
                self.send_data_to_redis(time.time()*1000, data_dict)

            # gyro
            case 507:
                gyro_data = gyro_data_live(queue, self.gyro_filter)
            
            # gps
            case 509:
                gps_data = gps_data_live(queue, self.gps_filter)
                frame_to_send = gps_data

            case 600:
                ecu_frame_0 = engine_data0_live(queue, self.theoretical_heat_prev)
                self.theoretical_heat_prev = ecu_frame_0['theoretical_heat']
                frame_to_send = ecu_frame_0

            case 602:
                ecu_frame_2 = engine_data2_live(queue)
                frame_to_send = ecu_frame_2

            case 603:
                ecu_frame_3 = engine_data3_live(queue)
                frame_to_send = ecu_frame_3

            case 604:
                ecu_frame_4 = engine_data4_live(queue)
                frame_to_send = ecu_frame_4

            case 606:
                ecu_frame_6 = engine_data6_live(queue)
                frame_to_send = ecu_frame_6

            case _:
                pass

        if frame_to_send is not None:
            self.send_data_to_redis(timestamp, frame_to_send)


    def init_previous_values(self):
        self.theoretical_heat_prev = -1.

    def init_filters(self):
        self.gyro_filter = GYROKalman()
        self.gps_filter = GPSKalman()
        self.acc_filter = ACCKalman()
        self.lap_timer = LapTimer()

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