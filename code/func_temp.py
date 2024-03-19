import csv
import os
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *
from kalman_filters import *
from test_functions.filters import FirFilter, get_alpha, low_pass_filter

path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-02-25 proto/cooling/'

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
    delta_rr_in = 0.
    delta_lr_in = 0.
    delta_rr_out = 0.
    delta_lr_out = 0.
    delta_engine_in = 0.
    delta_engine_out = 0.
    fir_filters = []
    fir_window = 10

    f_temp = list(range(6))

    for i in range(6):
        fir_filters.append(FirFilter([1/fir_window for _ in range(fir_window)]))
    startTime = datetime.datetime.now()
    row_counter = 0

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

        f_temp = kalman_temp(f_temp, float(row['engine_in']), float(row['engine_out']), float(row['radiator_l_in']), float(row['radiator_l_out']), float(row['radiator_r_in']),float(row['radiator_r_out']), row_counter)

        engine_delta = f_temp[1].x[0][0] - f_temp[0].x[0][0]
        left_radiator_delta = f_temp[3].x[0][0] - f_temp[2].x[0][0]
        right_radiator_delta = f_temp[5].x[0][0] - f_temp[4].x[0][0]
        #if row_counter > 1:
            #timestep = float(row['timestamp']) - time_prev
            #delta_rr_in = temp_differentiate(rr_in_prev, float(row['radiator_r_in']), timestep, fir_filters[0])
            #delta_lr_in = temp_differentiate(lr_in_prev, float(row['radiator_l_in']), timestep, fir_filters[1])
            #delta_rr_out = temp_differentiate(rr_out_prev, float(row['radiator_r_out']), timestep, fir_filters[2])
            #delta_lr_out = temp_differentiate(lr_out_prev, float(row['radiator_l_out']), timestep, fir_filters[3])
            #delta_engine_in = temp_differentiate(engine_in_prev, float(row['engine_in']), timestep, fir_filters[4])
            #delta_engine_out = temp_differentiate(engine_out_prev, float(row['engine_out']), timestep, fir_filters[5])

        rr_in_prev = float(row['radiator_r_in'])
        rr_out_prev = float(row['radiator_r_out'])
        lr_in_prev = float(row['radiator_l_in'])
        lr_out_prev = float(row['radiator_l_out'])
        engine_in_prev = float(row['engine_in'])
        engine_out_prev = float(row['engine_out'])
        time_prev = float(row['timestamp'])

        if float(row['engine_out']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("out", f_temp[1].x[0][0])
                .field("out_delta6", f_temp[1].x[1][0])
                .time(timestamp)
            )
            points.append(point)
        if float(row['engine_in']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'engine')
                .field("in", f_temp[0].x[0][0])
                .field("in_delta6", f_temp[0].x[1][0])
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
                .field("in", f_temp[2].x[0][0])
                .field("in_delta6", f_temp[2].x[1][0])
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_l_out']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_l')
                .field("out", f_temp[3].x[0][0])
                .field("out_delta6", f_temp[3].x[1][0])
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
                .field("in", f_temp[4].x[0][0])
                .field("in_delta6", f_temp[4].x[1][0])
                .time(timestamp)
            )
            points.append(point)
        if float(row['radiator_r_out']) != -1.:
            point = (
                Point('temp')
                .tag("temperature", 'radiator_r')
                .field("out", f_temp[5].x[0][0])
                .field("out_delta6", f_temp[5].x[1][0])
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