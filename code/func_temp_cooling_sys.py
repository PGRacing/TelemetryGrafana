import csv
import os
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *
from kalman_filters import *
from data_filtration import *
from func_can import *
from func_ecumaster import *
from heat import *
from test_functions.filters import FirFilter, get_alpha, low_pass_filter

path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-05-14 Pszczolki/cooling/'
folder_path_can = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-05-14 Pszczolki/can/'
folder_path_ecumaster = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-05-14 Pszczolki/ecumaster/'

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
    last_ecumaster_file = 0

    startProgram = datetime.datetime.now()
    for item in os.listdir(path):
        full_path = os.path.join(path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            file_counter += 1
            open_file(full_path, last_ecumaster_file)
    endProgram = datetime.datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram-startProgram}!')


def open_file(filefullpath, last_ecumaster_file):
    file = open(filefullpath, "r")
    csv_reader = csv.DictReader(file)
    points = []
    temp_data = TEMPKalman()
    heat = Heat()

    startTime = datetime.datetime.now()
    row_counter = 0
    last_line_match_can = 0
    last_line_match_ecumaster = 0
    clt = -1
    heat_left_prev = 0
    heat_right_prev = 0
    heat_engine_prev = 0
    time_delta = 1
    engine_heat = 0
    left_heat = 0
    right_heat = 0 
    ecumaster_match = False

    if os.path.exists(folder_path_can):
        can_file = match_file(file_counter)
        

    for row in csv_reader:
        if row_counter <= 2:
            row_counter += 1
            #if row_counter == 2:
            #    clt, last_ecumaster_file, last_line_match = find_ecumaster_file(folder_path_ecumaster, last_ecumaster_file, float(row['timestamp']))
            continue
        try:
            float(row['timestamp'])
            float(row['radiator_r_out'])
        except (ValueError, TypeError) as e:
            continue 
        timestamp = datetime.datetime.fromtimestamp(float(row['timestamp'])) - datetime.timedelta(hours=2)

        '''finindig matching ecumaster data'''
        clt, last_ecumaster_file, last_line_match_ecumaster = find_ecumaster_file(folder_path_ecumaster, last_ecumaster_file,last_line_match_ecumaster, float(row['timestamp']))
        if clt != -1:
            ecumaster_match = True


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

            if (temp_data.f[0].x[1][0]*60 > 100):
                continue

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

            '''calculating heat(with engine if match in timestamp was found)'''

            if os.path.exists(folder_path_can) and ecumaster_match and clt != -1:
                left_heat, right_heat, engine_heat, last_line_match_can = calc_heat_radiators_and_engine(can_file, last_line_match_can, abs(left_radiator_delta), abs(right_radiator_delta), clt - (temp_data.f[5].x[0][0] + temp_data.f[3].x[0][0])/2, float(row['timestamp']), heat)
                heat_radiators_derivative = calc_derivative(left_heat+right_heat, heat_right_prev+heat_left_prev, time_delta)
                heat_engine_derivative = calc_derivative(engine_heat, heat_engine_prev, time_delta)
            else:
                left_heat, right_heat, last_line_match_can = calc_heat_radiators(can_file, last_line_match_can, abs(left_radiator_delta), abs(right_radiator_delta), float(row['timestamp']), heat)
                heat_radiators_derivative = calc_derivative(left_heat+right_heat, heat_right_prev+heat_left_prev, time_delta)

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

                point = (
                    Point('engine')
                    .tag("radiator", 'heat')
                    .field('derivative_r', heat_radiators_derivative)
                    .time(timestamp)
                )
                points.append(point)

                if ecumaster_match:
                    point = (
                        Point('engine')
                        .tag("radiator", 'heat')
                        .field('engine', engine_heat)
                        .time(timestamp)
                    )
                    points.append(point)


                    point = (
                        Point('engine')
                        .tag("radiator", 'heat')
                        .field('derivative_e', heat_engine_derivative)
                        .time(timestamp)
                    )
                    points.append(point)

        

        if row_counter % 200 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        row_counter += 1
        heat_engine_prev = engine_heat
        heat_left_prev = left_heat
        heat_right_prev = right_heat

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
        


def find_ecumaster_file(path, last_file_index, last_line_match, timestamp_cooling):
    file_counter = 0
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        if file_counter >= last_file_index:
            clt, last_line_match = open_ecu_and_match(full_path, last_line_match, timestamp_cooling)
            file_counter += 1
            if clt != -1:
                return clt, last_file_index, last_line_match
    return clt, last_file_index, last_line_match


def open_ecu_and_match(file_path, last_line_match, timestamp_cooling):
    with open(file_path, 'r') as file:
        data = csv.DictReader(file, delimiter=';')
        split_path = file_path.split("/")
        filename = split_path[-1]
        start_time = find_start_time(filename)
        row_counter = 0
        for row in data:
            if row_counter >= last_line_match:
                second = float(row['TIME'].replace(',', '.'))
                seconds_timedelta = datetime.timedelta(seconds=second)
                timestamp = start_time + seconds_timedelta
                ecumaster_timestamp = timestamp.timestamp()
                
                if (abs(ecumaster_timestamp - timestamp_cooling) < 1.1):
                    return float(row['CLT']), row_counter
            row_counter += 1
        return -1, 0
    
def calc_heat_radiators_and_engine(can_file, last_line_match, delta_left, delta_right, engine, timestamp, heat):
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
                        engine_heat = heat.calc_water_heat(engine, flow_right + flow_left)
                        return left_heat, right_heat, engine_heat, row_counter
                else:
                    row_counter += 1
        return -1, -1, -1, last_line_match
    

def calc_derivative(current, previous, time_delta):
    derivative = (current - previous) / time_delta
    return derivative


def cooling_data(data, timestamp, heat, temperature, flow, clt, heat_prev_values, points):
    # TODO decode data

    ''' radiators and engine temperature '''

    temperature.filter_temperature(engine_in, engine_out, radiator_l_in, radiator_l_out, radiator_r_in, radiator_r_out)

    engine_delta = temperature.f[1].x[0][0] - temperature.f[0].x[0][0]
    left_radiator_delta = temperature.f[3].x[0][0] - temperature.f[2].x[0][0]
    right_radiator_delta = temperature.f[5].x[0][0] - temperature.f[4].x[0][0]

    ''' heat based on temperature delta '''

    (flow_left, flow_right) = flow
    (heat_left_prev, heat_right_prev, heat_engine_prev) = heat_prev_values

    left_heat = heat.calc_water_heat(abs(left_radiator_delta), flow_left)
    right_heat = heat.calc_water_heat(abs(right_radiator_delta), flow_right)
    engine_heat = heat.calc_water_heat(clt - (temperature.f[5].x[0][0] + temperature.f[3].x[0][0])/2, flow_right + flow_left)
    heat_radiators_derivative = calc_derivative(left_heat+right_heat, heat_right_prev+heat_left_prev, 1)
    heat_engine_derivative = calc_derivative(engine_heat, heat_engine_prev, 1)

    
    point = (
        Point('temp')
        .tag("temperature", 'engine')
        .field("out", temperature.f[1].x[0][0])
        .field("out_delta", temperature.f[1].x[1][0]*60)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('temp')
        .tag("temperature", 'engine')
        .field("in", temperature.f[0].x[0][0])
        .field("in_delta", temperature.f[0].x[1][0]*60)
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
        .field("in", temperature.f[2].x[0][0])
        .field("in_delta", temperature.f[2].x[1][0]*60)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('temp')
        .tag("temperature", 'radiator_l')
        .field("out", temperature.f[3].x[0][0])
        .field("out_delta", temperature.f[3].x[1][0]*60)
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
        .field("in", temperature.f[4].x[0][0])
        .field("in_delta", temperature.f[4].x[1][0]*60)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('temp')
        .tag("temperature", 'radiator_r')
        .field("out", temperature.f[5].x[0][0])
        .field("out_delta", temperature.f[5].x[1][0]*60)
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

    point = (
        Point('engine')
        .tag("radiator", 'heat')
        .field('derivative_r', heat_radiators_derivative)
        .time(timestamp)
    )
    points.append(point)

    if ecumaster_match:
        point = (
            Point('engine')
            .tag("radiator", 'heat')
            .field('engine', engine_heat)
            .time(timestamp)
        )
        points.append(point)


        point = (
            Point('engine')
            .tag("radiator", 'heat')
            .field('derivative_e', heat_engine_derivative)
            .time(timestamp)
        )
        points.append(point)






if __name__ == '__main__':
    find_file(path)
