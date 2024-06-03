import can
import os
import struct
import datetime
from func_can import *
from func_ecumaster import *
from func_temp_cooling_sys import *

folder_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/00000001.MF4'

def find_files(folder_path):
    startProgram = datetime.datetime.now()
    file_counter = 0
    for item in os.listdir(folder_path):
        full_path = os.path.join(folder_path, item)

        if os.path.isfile(full_path):
            file_counter += 1
            iterate_file(full_path)
    endProgram = datetime.datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram - startProgram}!')

def iterate_file(file_path):
    temp_data = TEMPKalman()
    heat = Heat()
    line_counter = 0
    points = []
    start_time = datetime.datetime.now()
    try:
        for msg in can.LogReader(file_path):
            print(msg)
            timestamp = msg.timestamp
            arbitration_id = int(f"{msg.arbitration_id:X}")

            # our sensors
            if msg.channel == 1:
                match arbitration_id:
                    # wheel speed sensor (abs) front
                    case 503:
                        pass

                    # damper front 
                    case 504:
                        pass

                    # gyro front
                    case 507:
                        pass

                    # acc front
                    case 508:
                        pass

                    # gps
                    case 509:
                        pass

                    # wheel speed sensor (abs) rear
                    case 603:
                        pass

                    # damper rear
                    case 604:
                        pass

                    # gyro back
                    case 607:
                        pass

                    # acc back
                    case 608:
                        pass

                    # flow
                    case 609:
                        flow = flow_data(msg.data, timestamp, points)
            # ecumaster
            else:
                match arbitration_id:
                    case 600:
                        theoretical_heat_prev = engine_data1(msg.data, timestamp, theoretical_heat_prev, points)
                    case 602:
                        clt = engine_data2(msg.data, timestamp, points)
                    case 606:
                        engine_data6(msg.data, timestamp, points)



            


            if line_counter % 1300 == 0:
                write_api.write(bucket=bucket, org=org, record=points)
                points.clear()



        write_api.write(bucket=bucket, org=org, record=points)
        end_time = datetime.datetime.now()
        print(f'{line_counter} sent in {end_time - start_time}')


    except ValueError as e:
        pass


if __name__ == '__main__':
    iterate_file(folder_path)