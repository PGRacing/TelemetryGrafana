import redis
import struct
import time
import websockets
import json
import asyncio
import functools
from pathlib import Path
import sys
from multiprocessing import Process, Queue

directory = Path(__file__).absolute()
 
# setting path
sys.path.append(f'{directory.parent.parent}')

from func_imu import gyro_data_live
from func_gps import gps_data_live
from func_abs import vss_data_live
from lap_timer import LapTimer
from func_ecumaster import *
from data_filtration import *

class Redis:
    def __init__(self, queue):
       # self.queue_to_websocket = Queue()
        self.redis_process = Process(target=self.start_redis, args=(queue,))
       # self.websocket_process = Process(target=websocket_handler, args=(self.queue_to_websocket,))
        self.redis_process.start()
       # self.websocket_process.start()

    # Redis server -------------------------------------

    def start_redis(self, queue):  
        self.r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        print('Redis started.')

        self.init_previous_values()
        self.init_filters()

        while True:
            id_bytes = bytearray()
            for i in range(2):
                id_bytes.extend([queue.get()])
            id = int(struct.unpack('<H', id_bytes)[0])
            
            print(type(id))
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

       # print(f'{type(id)}')
      #  print(type(0x5))

        match id:
            # test case (counter)
            case 0x5:
                data_bytes = bytearray()
                for i in range (2):
                    data_bytes.extend([queue.get()])
                data = struct.unpack('>H', data_bytes)[0]

                data_dict = {'counter':str(data)}
                    
                self.send_data_to_redis(time.time()*1000, data_dict)

            # vss front
            case 0x503:
                vss_data = vss_data_live(queue, self.prev_speed_front, True)
                self.prev_speed_front = (vss_data['front_left_speed'], vss_data['front_right_speed'])
                frame_to_send = vss_data

            # vss rear
            case 0x504:
                vss_data, self.prev_speed_rear = vss_data_live(queue, self.prev_speed_rear, False)
                frame_to_send = vss_data

            # gyro
            case 0x507:
                gyro_data = gyro_data_live(queue, self.gyro_filter)
            
            # gps
            case 0x509:
                gps_data = gps_data_live(queue, self.gps_filter, self.lap_timer)
                frame_to_send = gps_data

                if self.initial_gps_coordinates_set == False:
                    self.lap_timer.init_position(gps_data['lon'], gps_data['lat'], timestamp)
                    self.initial_gps_coordinates_set = True
                else:
                    last_lap_time, lap_diff, lap_counter, lap_duration_time = self.lap_timer.check(gps_data['lon'], gps_data['lat'], timestamp)

                if (last_lap_time < best_time and lap_counter != 0) or lap_counter == 1:
                    best_time = last_lap_time
                    best_lap_number = lap_counter

            # ecumaster
            case 0xe00:
                print('ECU frame 0')
                ecu_frame_0 = engine_data0_live(queue, self.theoretical_heat_prev)
             #   self.theoretical_heat_prev = ecu_frame_0['theoretical_heat']
                frame_to_send = ecu_frame_0

            case 0xe02:
                ecu_frame_2 = engine_data2_live(queue)
                frame_to_send = ecu_frame_2

            case 0xE03:
                ecu_frame_3 = engine_data3_live(queue)
                frame_to_send = ecu_frame_3

            case 0xE04:
                ecu_frame_4 = engine_data4_live(queue)
                frame_to_send = ecu_frame_4

            case 0xE06:
                ecu_frame_6 = engine_data6_live(queue)
                frame_to_send = ecu_frame_6

            case _:
                pass

        if frame_to_send is not None:
            self.send_data_to_redis(timestamp, frame_to_send)
            frame_to_send['timestamp'] = timestamp
           # self.queue_to_websocket.put(frame_to_send)


    def init_previous_values(self):
        self.theoretical_heat_prev = -1.
        self.prev_speed_front = None
        self.prev_speed_rear = None

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

            data_dict = {'counter': value}
            self.send_data_to_redis(time.time()*1000, data_dict)

    def send_data_to_redis(self, timestamp, data):
        for key, value in data.items():
            self.r.xadd(key, fields={'value': value, 'timestamp': timestamp})
    

    
