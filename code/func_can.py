import csv
import struct
import datetime
import base64
from conf_influxdb import *

folder_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-04-30 proto - test can/can/'

'''
WIELKIE TODO 

1. Reczne korekcje czasu można olać i na grafanie ustawić czas GMT (nie trzeba po zmianie czasu zmieniać na -2h)
2. Przepływ jest w l/min

'''

def find_can_files(folder_path):
    startProgram = datetime.datetime.now()
    file_counter = 0
    for item in os.listdir(folder_path):
        full_path = os.path.join(folder_path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            file_counter += 1
            import_csv_can(full_path)
    endProgram = datetime.datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram - startProgram}!')

def import_csv_can(path):
    line_count = 1
    points = []
    startTime = datetime.datetime.now()
    with open(path, 'r') as file:
        data = csv.DictReader(file)
        for row in data:
            try:
                float(row['timestamp'])
            except(ValueError, TypeError) as e:
                continue

            timestamp = datetime.datetime.fromtimestamp(float(row['timestamp'])) - datetime.timedelta(hours=2)
            flow_left, flow_right = calc_flow_on_radiators(row['arbitration_id'], row['data'], int(row['error']))

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

            if line_count % 2000 == 0:
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
    
if __name__ == '__main__':
    find_can_files(folder_path)