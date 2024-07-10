import csv
import sys
import struct
import datetime
import base64
from conf_influxdb import *
from heat import *

folder_path_can = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-05-14 Pszczolki/can/'
folder_path_cooling = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-05-14 Pszczolki/cooling/'

'''
WIELKIE TODO 

1. Reczne korekcje czasu można olać i na grafanie ustawić czas GMT (nie trzeba po zmianie czasu zmieniać na -2h/-1h)

'''


def find_can_files(folder_path):
    startProgram = datetime.datetime.now()
    file_counter = 0
    for item in os.listdir(folder_path):
        full_path = os.path.join(folder_path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            file_counter += 1
            import_csv_can(full_path, file_counter)
    endProgram = datetime.datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram - startProgram}!')

def import_csv_can(path, file_counter):
    heat = Heat()
    line_count = 1
    points = []
    startTime = datetime.datetime.now()
    last_line_match = 0
    with open(path, 'r') as file:
        data = csv.DictReader(file)
        cooling_file = match_file(file_counter)
        for row in data:
            try:
                float(row['timestamp'])
                int(row['error'])
            except(ValueError, TypeError) as e:
                continue

            timestamp = datetime.datetime.fromtimestamp(float(row['timestamp'])) - datetime.timedelta(hours=2)
            flow_left, flow_right = calc_flow_on_radiators(row['arbitration_id'], row['data'], int(row['error']))
          #  flow_engine = calc_flow_on_radiators(row['arbitration_id'], row['data'], int(row['error']))
            #delta_l, delta_r, timestep, last_line_match = match_cooling_log(cooling_file, float(row['timestamp']), last_line_match)
            #if delta_l != -1 and delta_r != -1 and timestep != -1:
            #    left_radiator_heat = heat.calc_water_heat(delta_l, flow_left, timestep)
            #    right_radiator_heat = heat.calc_water_heat(delta_r, flow_right, timestep)

            #    point = (
            #        Point('engine')
            #        .tag("radiator", 'heat')
            #        .field('right', right_radiator_heat)
            #        .time(timestamp)
            #    )
            #    points.append(point)

            #    point = (
            #        Point('engine')
            #        .tag("radiator", 'heat')
             #       .field('left', left_radiator_heat)
            #        .time(timestamp)
            #    )
            #    points.append(point)

            if (flow_left != -1 and flow_right != -1):
                point = (
                    Point('CAN')
                    .tag("ID", '0x609')
                    .field("flow_right", float(flow_right))
                    .time(timestamp)
                )
                points.append(point)

                point = (
                    Point('CAN')
                    .tag("ID", '0x609')
                    .field("flow_left", float(flow_left))
                    .time(timestamp)
                )
                points.append(point)

                

            if line_count % 1300 == 0:
                write_api.write(bucket=bucket, org=org, record=points)
                points.clear()
            line_count += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.datetime.now()
    print(f'CAN: Imported {line_count} rows in {endTime - startTime}')

def calc_flow_on_radiators(arbitration_id, data, error):
    if (arbitration_id == '0x609' and error == 0):
        '''base64 to bytes'''
        decoded_bytes = base64.b64decode(data)
        '''
        <   Little Endian Byte Order
        H   unsigned short (uint16), first 2 bytes
        H   unsigned short (uint16), next 2 bytes
        '''
        left, right = struct.unpack('<HH', decoded_bytes)
        left /= 32.
        right /= 32.
        return left, right
    else:
        return -1, -1
    

'''

Matching with cooling files to falculate heat on radiators.

'''
    
def match_file(desired_file_number):
    file_counter = 0
    for item in os.listdir(folder_path_can):
        if file_counter == desired_file_number:
            full_path = os.path.join(folder_path_can, item)
            return full_path
        file_counter += 1
    
def match_cooling_log(cooling_file, timestamp, last_line_match):
    with open(cooling_file, 'r') as file:
        data = csv.DictReader(file)
        line_counter = 0
        for row in data:
            line_counter += 1
            if line_counter >= last_line_match:
                try:
                    timestep = abs(timestamp - float(row['timestamp']))
                    if (timestep < 1.):
                        delta_l = float(row['radiator_l_out']) - float(row['radiator_l_in'])
                        delta_r = float(row['radiator_r_out']) - float(row['radiator_r_in'])
                        return delta_l, delta_r, timestep
                except ValueError as e:
                    return -1, -1, -1, last_line_match
    return -1, -1, -1, last_line_match

'''

Functions to apply for reading from logger.

'''

def flow_data(data, timestamp, points):
    '''
    <   Little Endian Byte Order
    H   unsigned short (uint16), first 2 bytes
    H   unsigned short (uint16), next 2 bytes
    '''
    left, right = struct.unpack('<HH', data)
    left /= 32.
    right /= 32.

    point = (
        Point('CAN')
        .tag("ID", 'flow')
        .field("flow_right_radiator", right)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('CAN')
        .tag("ID", 'flow')
        .field("flow_left_radiator", left)
        .time(timestamp)
    )
    points.append(point)


    return left, right


'''
Live telemetry.
'''
def flow_data_live(queue):
    '''
    <   Little Endian Byte Order
    H   unsigned short (uint16), first 2 bytes
    H   unsigned short (uint16), next 2 bytes
    '''
    flow_multiplier = 32.
    data = bytearray()
    
    for i in range(4):
        data.extend([queue.get()])
    left, right = struct.unpack('<HH', data)
    left /= flow_multiplier
    right /= flow_multiplier

    data_to_send = {
        "flow_right_radiator": left,
        "flow_left_radiator": right,
    }

    return data_to_send





if __name__ == '__main__':
    find_can_files(folder_path_can)