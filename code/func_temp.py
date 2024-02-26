import datetime
import csv
from conf_influxdb import *
from utils_timestamp import *

path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24_02_25_proto/'

file_counter = 0

def find_file(filepath):
    global file_counter

    #startProgram = datetime.datetime.now()
    for i in range (1, 83):
        file_counter += 1
        if file_counter == 71 or file_counter == 72 or file_counter == 74:
            continue
        open_file(filepath + 'cooling_system_temp_' + str(i) + '.csv')
    #endProgram = datetime.now()
    print(f'Successfully imported {file_counter} files !')


def open_file(filefullpath):
    file = open(filefullpath, "r")
    csv_reader = csv.DictReader(file)
    points = []
        
    #startTime = datetime.now()
    row_counter = 0

    for row in csv_reader:
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

        engine_delta = float(row['engine_out']) - float(row['engine_in'])
        left_radiator_detla = float(row['radiator_l_out']) - float(row['radiator_l_in'])
        right_radiator_delta = float(row['radiator_r_out']) - float(row['radiator_r_in'])

        point = (
            Point('temp')
            .tag("temperature", 'engine')
            .field("out", float(row['engine_out']))
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('temp')
            .tag("temperature", 'engine')
            .field("in", float(row['engine_in']))
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
            .field("in", float(row['radiator_l_in']))
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('temp')
            .tag("temperature", 'radiator_l')
            .field("out", float(row['radiator_l_out']))
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('temp')
            .tag("temperature", 'radiator_l')
            .field("delta", left_radiator_detla)
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('temp')
            .tag("temperature", 'radiator_r')
            .field("in", float(row['radiator_r_in']))
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('temp')
            .tag("temperature", 'radiator_r')
            .field("out", float(row['radiator_r_out']))
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

        if row_counter % 200 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        row_counter += 1

    write_api.write(bucket=bucket, org=org, record=points)
    #endTime = datetime.datetime.now()
    print(f'Calculated file number {file_counter} in')

find_file(path)