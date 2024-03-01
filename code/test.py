import csv
import datetime
from utils_timestamp import *
from func_gps import *
from func_damp import *

filepath = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/23_11_05_Pszczolki/'


start_lap = datetime.datetime(year=2023, month=11, day=5, hour=9, minute=54, second=13, microsecond=640000)

#start_time, time_coefficients = import_csv_gps(filepath + 'GPS0101-27.csv')
#damp_data = import_csv_damp(filepath + 'DAMP0101-27.csv', start_time, time_coefficients, start_lap)
f = open("items.txt", "r")
d = f.readlines()
data = []
temp = []
first_transformation = d[0].split()
print(len(first_transformation))
for i in range(0, len(first_transformation)):
    temp.append(float(first_transformation[i]))
    if i % 2 == 1:
        data.append(temp)
        temp = []
angles = []


with open('lap_53_no_steering_wheel.csv', 'r') as read_file:
    data_csv = csv.DictReader(read_file)
    #print(f'racebox data: {len(data)}')
    for row in data_csv:
        added = False
        for i in range (0, len(data)):
            if added == False and abs(float(row['seconds']) - data[i][0]) < 0.01 or ((abs(float(row['seconds']) - data[i][0]) > 59.) and (abs(float(row['seconds']) - data[i][0]) < 60.)):
                angles.append(data[i][1])
                added = True
                break


print(f'angles: {len(angles)}')

with open('lap_53_no_steering_wheel.csv', 'r') as read_file:
    with open('lap_53.csv', 'w') as save_file:
        reader = csv.reader(read_file)
        writer = csv.writer(save_file)
        writer.writerow(['acc_x', 'acc_y', 'acc_z', 'speed', 'steering_wheel_angle'])
        next(reader)
        next(reader)
        row_counter = 0
        real_row_counter = 0
        for row in reader:
            empty_row = False
            if real_row_counter < 7:
                print(real_row_counter)
                print(row)
            if row_counter % 2 == 1:
                #next(reader)
                empty_row = True
                
            if real_row_counter>584:
                print(real_row_counter)
                print(row)

            if not empty_row:
                steering_wheel_angle_value = angles[real_row_counter]
                modified_row = row[1:] + [steering_wheel_angle_value]
                writer.writerow(modified_row)
                real_row_counter += 1
            row_counter += 1
