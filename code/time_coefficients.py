import datetime
import csv
from utils_timestamp import *

filepath = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/23_11_05_Pszczolki/'

def set_time_coefficients():
    for i in range(1, 34):
        coefficient = calc_time_variance_gps(filepath + 'GPS0101-' + str(i) + '.csv', i)
        print(f'Time variance for file {str(i)}: {coefficient}')

def calc_time_variance_gps(filepath, file_num):
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
                if utc_time_value and speed_numerical_value and ((float(row["speed"]) * 1.852) > 0.2):
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

set_time_coefficients()






