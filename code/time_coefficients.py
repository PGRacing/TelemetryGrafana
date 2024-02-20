import datetime
import csv
from utils_timestamp import *
from func_damp import *

filepath = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/23_11_05_Pszczolki/'

# GPS timestep 0.04
# DAMP timestep 0.004

def set_time_coefficients():
    for i in range(1, 34):
        coefficient = calc_time_diff_factor_gps(filepath + 'GPS0101-' + str(i) + '.csv')
        #coefficient_damp = calc_time_diff_factor(filepath + 'DAMP0101-' + str(i) + '.csv', i)
        print(f'Time variance for file {str(i)}: {coefficient}')

def calc_time_diff_factor_gps(filepath):
    with open(filepath, 'r') as file:
        csv_reader = csv.DictReader(file)
        row_counter = 0
        start_set = finish_set = False
        for row in csv_reader:
            #print(f'row: {row_counter}, utc: {row["utc"]}, timestamp: {row["timestamp"]}')
            speed_numerical_value = utc_time_value = True
            if row['utc'] and row['speed']and (start_set == False):
                try:
                    x = float(row["utc"])
                    x = float(row["speed"])
                except (TypeError, ValueError):
                    utc_time_value = False
                    speed_numerical_value = False
                if utc_time_value and speed_numerical_value and ((float(row["speed"]) * 1.852) > 2.):
                    utc_start = gps_utc_to_timedelta(row['utc'])
                    timestamp_start = csv_timestamp_to_timedelta(row['timestamp'])
                    start_row = row_counter
                    start_set = True
                    #print(f'utc: {utc_start}, timestamp: {timestamp_start}')

            if row['speed'] and row['utc'] and row['speed']:
                try:
                    x = float(row["speed"])
                except (TypeError, ValueError):
                    speed_numerical_value = False
                    #print(f'file: {file_num} row: {row_counter + 1}')
                if speed_numerical_value and ((float(row["speed"]) * 1.852) < 1.3) and start_set and(row_counter-start_row > 1000):
                        utc_end = gps_utc_to_timedelta(row['utc'])
                        timestamp_end = csv_timestamp_to_timedelta(row['timestamp'])
                        finish_set = True
                        #print(f'utc: {utc_end}, timestamp: {timestamp_end}')
            row_counter += 1
        
            if start_set and finish_set:
                utc_diff = utc_end - utc_start
                #print(utc_diff)
                timestamp_diff = timestamp_end - timestamp_start
                coeff = utc_diff.total_seconds() / timestamp_diff.total_seconds()
                return coeff
            
def calc_time_diff_factor(filepath, filenum):
    with open(filepath, 'r') as file:
        csv_reader = csv.DictReader(file)
        start_set = finish_set = False
        data = []
        for row in csv_reader: 
            if int(row['ID']) == 6:
                wheel_position = calc_wheel_position(row)
                timestamp = csv_timestamp_to_timedelta(row['timestamp'])
                data.append([timestamp, wheel_position])
        #print(len(data))
        for i in range(30, len(data)):
            if (abs(data[i][1] -data[i-30][1]) > 30) and start_set == False:
                start_timestamp = data[i-30][0]
                start_set = True
                utc_start = match_utc_time(filenum, start_timestamp)
                print(f'start: {utc_start}')
        for i in range(1000, len(data)):
            if (abs(data[i][1] - data[i-1000][1]) < 5) and finish_set == False and start_set and data[i-1000][0] > start_timestamp:
                for i in range(1, 1000):
                    if abs(data[i][1] - data[i-1][1]) > 5:
                        break
                finish_timestamp = data[i-1000][0]
                finish_set = True
                utc_finish = match_utc_time(filenum, finish_timestamp)
                print(f'finish: {utc_finish}')
                
        
        if start_set and finish_set:
                utc_diff = utc_finish - utc_start
                timestamp_diff = finish_timestamp - start_timestamp
                coeff = utc_diff.total_seconds() / timestamp_diff.total_seconds()
                return coeff


# TODO find the closest utc time if the real closest is empty/not time
def match_utc_time(file_num, timestamp):
    with open(filepath + 'GPS0101-' + str(file_num) + '.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        buffor = 0.03
        incorrect_timestamp = False
        for row in csv_reader:
            date_format_correct = True
            try:
                csv_timestamp_to_timedelta(row['timestamp'])
            except (TypeError, ValueError):
                date_format_correct = False
            if row['utc'] == '':
                buffor = 0.15
                incorrect_timestamp = True
            if row['utc'] and date_format_correct and abs(csv_timestamp_to_timedelta(row['timestamp']) - timestamp).total_seconds() <= buffor:
                print(abs(csv_timestamp_to_timedelta(row['timestamp']) - timestamp).total_seconds())
                utc_time = gps_utc_to_timedelta(row['utc'])
                if incorrect_timestamp:
                    incorrect_timestamp = False
                    buffor = 0.04
                return utc_time 

#match_utc_time(12)
set_time_coefficients()






