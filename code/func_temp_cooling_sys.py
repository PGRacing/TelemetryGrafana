import csv
import os
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *
from kalman_filters import *
from data_filtration import *
from test_functions.filters import FirFilter, get_alpha, low_pass_filter

path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-16 proto/cooling/'

file_counter = 0

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
    def temp_differentiate(prev, current, timestep, filter):
        value = (current - prev)/timestep
        prev_diff = filter.get_last_value()
        value = filter.filter(value if abs(value) < 2.0 else 0.0)
        return low_pass_filter(prev_diff, value, get_alpha(1.0, 0.5))

    file = open(filefullpath, "r")
    csv_reader = csv.DictReader(file)
    points = []
    temp_data = TEMPKalman()

    startTime = datetime.datetime.now()
    row_counter = 0

    temp_data.init_kalman()

    for row in csv_reader:
        if row_counter == 0:
            row_counter += 1
            continue
        #print(datetime.datetime.fromtimestamp(float(row['timestamp'])))
        try:
            timestamp = datetime.datetime.fromtimestamp(float(row['timestamp'])) - datetime.timedelta(hours=1)
            float(row['engine_out'])
            float(row['engine_in'])
            float(row['radiator_l_in'])
            float(row['radiator_l_out'])
            float(row['radiator_r_in'])
            float(row['radiator_r_out'])
        except (ValueError, TypeError) as e:
            #print(e)
            continue 

        temp_data.filter_temperature(float(row['engine_in']), float(row['engine_out']), float(row['radiator_l_in']), float(row['radiator_l_out']), float(row['radiator_r_in']),float(row['radiator_r_out']))
        #f_temp = kalman_temp(f_temp, float(row['engine_in']), float(row['engine_out']), float(row['radiator_l_in']), float(row['radiator_l_out']), float(row['radiator_r_in']),float(row['radiator_r_out']), row_counter)

        engine_delta = temp_data.f[1].x[0][0] - temp_data.f[0].x[0][0]
        left_radiator_delta = temp_data.f[3].x[0][0] - temp_data.f[2].x[0][0]
        right_radiator_delta = temp_data.f[5].x[0][0] - temp_data.f[4].x[0][0]

        if float(row['engine_out']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("out", temp_data.f[1].x[0][0])
                .field("out_delta7", temp_data.f[1].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)
        if float(row['engine_in']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("in", temp_data.f[0].x[0][0])
                .field("in_delta7", temp_data.f[0].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)
        if float(row['engine_in']) != -1. and float(row['engine_out']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("delta", engine_delta)
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_l_in']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_l')
                .field("in", temp_data.f[2].x[0][0])
                .field("in_delta7", temp_data.f[2].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_l_out']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_l')
                .field("out", temp_data.f[3].x[0][0])
                .field("out_delta7", temp_data.f[3].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_l_out']) != -1. and float(row['radiator_l_in']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_l')
                .field("delta", left_radiator_delta)
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_r_in']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_r')
                .field("in", temp_data.f[4].x[0][0])
                .field("in_delta7", temp_data.f[4].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_r_out']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_r')
                .field("out", temp_data.f[5].x[0][0])
                .field("out_delta7", temp_data.f[5].x[1][0]*60)
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_r_out']) != -1. and float(row['radiator_r_in']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_r')
                .field("delta", right_radiator_delta)
                .time(timestamp)
            )
            points.append(point)

        if row_counter % 200 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        row_counter += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.datetime.now()
    print(f'Calculated file number {file_counter} in {endTime-startTime}')

find_file(path)