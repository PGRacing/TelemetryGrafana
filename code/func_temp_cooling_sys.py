import csv
import os
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *
from kalman_filters import *
from data_filtration import *
from func_can import *
from heat import *
from test_functions.filters import FirFilter, get_alpha, low_pass_filter

path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-04-30 proto - test can/cooling/'
folder_path_can = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-04-30 proto - test can/can/'

file_counter = 0

def calc_heat_radiators(can_file, last_line_match, delta_left, delta_right, timestamp, heat):
    with open(can_file, 'r') as file:
        data = csv.DictReader(file)
        row_counter = 0
        for row in data:
            if (row['arbitration_id'] == '0x609'):
                if row_counter >= last_line_match:
                    try:
                        float(row['timestamp'])
                    except ValueError as e:
                        continue
                    timestep = abs(timestamp - float(row['timestamp']))
                    if (timestep < 1.):
                        flow_left, flow_right = calc_flow_on_radiators(row['arbitration_id'], row['data'], int(row['error'])) 
                        left_heat = heat.calc_water_heat(delta_left, flow_left)
                        right_heat = heat.calc_water_heat(delta_right, flow_right)
                        return left_heat, right_heat, row_counter
                else:
                    row_counter += 1
        return -1, -1, last_line_match

def find_file(path):
    global file_counter

    startProgram = datetime.datetime.now()
    for item in os.listdir(path):
        full_path = os.path.join(path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            file_counter += 1
            open_file(full_path)
    endProgram = datetime.datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram-startProgram}!')


def open_file(filefullpath):
    file = open(filefullpath, "r")
    csv_reader = csv.DictReader(file)
    points = []
    temp_data = TEMPKalman()
    heat = Heat()

    startTime = datetime.datetime.now()
    row_counter = 0
    last_line_match = 0

    if os.path.exists(folder_path_can):
        can_file = match_file(file_counter)

    for row in csv_reader:
        if row_counter <= 2:
            row_counter += 1
            continue
        try:
            float(row['timestamp'])
            float(row['radiator_r_out'])
        except (ValueError, TypeError) as e:
            continue 
        timestamp = datetime.datetime.fromtimestamp(float(row['timestamp'])) - datetime.timedelta(hours=2)

        if (float(row['engine_out']) != -1. and
            float(row['engine_in']) != -1. and
            float(row['radiator_l_in']) != -1. and
            float(row['radiator_l_out']) != -1. and
            float(row['radiator_r_in']) != -1. and
            float(row['radiator_r_out']) != -1.):
            temp_data.filter_temperature(float(row['engine_in']), float(row['engine_out']), float(row['radiator_l_in']), float(row['radiator_l_out']), float(row['radiator_r_in']),float(row['radiator_r_out']))

            engine_delta = temp_data.f[1].x[0][0] - temp_data.f[0].x[0][0]
            left_radiator_delta = temp_data.f[3].x[0][0] - temp_data.f[2].x[0][0]
            right_radiator_delta = temp_data.f[5].x[0][0] - temp_data.f[4].x[0][0]

            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("out", temp_data.f[1].x[0][0])
                .field("out_delta", temp_data.f[1].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("in", temp_data.f[0].x[0][0])
                .field("in_delta", temp_data.f[0].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("delta", engine_delta)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'radiator_l')
                .field("in", temp_data.f[2].x[0][0])
                .field("in_delta", temp_data.f[2].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'radiator_l')
                .field("out", temp_data.f[3].x[0][0])
                .field("out_delta", temp_data.f[3].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'radiator_l')
                .field("delta", left_radiator_delta)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'radiator_r')
                .field("in", temp_data.f[4].x[0][0])
                .field("in_delta", temp_data.f[4].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'radiator_r')
                .field("out", temp_data.f[5].x[0][0])
                .field("out_delta", temp_data.f[5].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('temp')
                .tag("temperature", 'radiator_r')
                .field("delta", right_radiator_delta)
                .time(timestamp)
            )
            points.append(point)

            if os.path.exists(folder_path_can):
                left_heat, right_heat, last_line_match = calc_heat_radiators(can_file, last_line_match, abs(left_radiator_delta), abs(right_radiator_delta), float(row['timestamp']), heat)
                if (right_heat != -1 and left_heat != -1):
                    point = (
                        Point('engine')
                        .tag("radiator", 'heat')
                        .field('right', right_heat)
                        .time(timestamp)
                    )
                    points.append(point)

                    point = (
                        Point('engine')
                        .tag("radiator", 'heat')
                        .field('left', left_heat)
                        .time(timestamp)
                    )
                    points.append(point)

        

        if row_counter % 200 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        row_counter += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.datetime.now()
    file.close()
    print(f'Calculated file number {file_counter} in {endTime-startTime}')

def match_file(desired_file_number):
    can_file_counter = 0
    for item in os.listdir(folder_path_can):
        can_file_counter += 1
        if can_file_counter == desired_file_number:
            full_path = os.path.join(folder_path_can, item)
            return full_path
        
if __name__ == '__main__':
    find_file(path)
