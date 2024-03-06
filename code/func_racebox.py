import numpy as np
import csv
from conf_influxdb import *
from kalman_filters import *
from variances import *
from lap_timer import *
import math
from datetime import datetime
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise


path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24_03_03_Pszczolki/racebox/'

GFORCE =  9.80665 # m/s2
TIMESTEP = 0.04 # s
file_counter = 0
lap_counter = 0
last_time = 0.
best_lap_number = 0
best_time = 0.
var_gyro = 0.
var_acc = 0.

special_lap_acc = []

# to be set every track change
approx_lon = 18.712
approx_lat = 54.178
lat_prev = 54.1784441
lon_prev = 18.7133100

conv_rate_lon = math.cos(approx_lat) * (40075000/360) # deg to met
conv_rate_lat = 111111.0


def find_racebox(filepath):
    global file_counter
    global var_gyro
    global var_acc
    global var_gps

    startProgram = datetime.now()
    for item in os.listdir(path):
        full_path = os.path.join(path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            file_counter += 1
            open_file(full_path)
    endProgram = datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram - startProgram}!')

def open_file(filefullpath):
    global lon_prev
    global lat_prev
    global lap_counter
    global best_lap_number
    global best_time
    global last_time
    global special_lap_acc
    
    with open(filefullpath, 'r') as file:
        lap_timer = LapTimer()
        data = csv.DictReader(file)
        points = []
        startTime = datetime.now()
        row_counter = 0
        inner_lap_counter = 0
        

        f_gps = list(range(3))
        f_acc = list(range(3))
        f_gyro = list(range(3))
        
        ang_vel_prev_x = 0.
        ang_vel_prev_y = 0.
        ang_vel_prev_z = 0.
        
        roll = 0.
        pitch = 0.
        yaw = 0.

        vel_x = 0.
        vel_y = 0.
        vel_z = 0.

        #acc_prev_x = 0.189
        #acc_prev_y = 0.037
        #acc_prev_z = 0.990

        for row in data:
            gyro_x = float(row['GyroX'])
            gyro_y = float(row['GyroY'])
            gyro_z = float(row['GyroZ'])

            GForceX = float(row['GForceX']) * GFORCE 
            GForceY = float(row['GForceY']) * GFORCE 
            GForceZ = float(row['GForceZ']) * GFORCE

            timestamp = row['Time']

    #vel_x = f_gps[0].x[1][0] * conv_rate_lon
    #vel_y = f_gps[1].x[1][0] * conv_rate_lat

            f_gps = kalman_gps(f_gps, float(row['Latitude']), float(row['Longitude']), row_counter)
            f_acc = kalman_acc(f_acc, GForceX, GForceY, GForceZ, (f_gps[1].x[1][0] * conv_rate_lon), (f_gps[0].x[1][0] * conv_rate_lat), row_counter)
            f_gyro, yaw = kalman_gyro(f_gps, f_gyro, f_acc, gyro_x, gyro_y, gyro_z, row_counter, lon_prev, lat_prev, yaw)
            
            if row_counter == 0:
                lap_timer.init_position(x=f_gps[1].x[0][0], y=f_gps[0].x[0][0], time=timestamp)
            else:
                last_time, lap_diff, inner_lap_counter = lap_timer.check(x=f_gps[1].x[0][0], y=f_gps[0].x[0][0], timestamp=timestamp)
                lap_counter += lap_diff
            if (last_time < best_time and inner_lap_counter != 0) or lap_counter == 1:
                    best_time = last_time
                    best_lap_number = lap_counter

            #if lap_counter == 53:
            #    time = row['Time'][17:23]
            #    special_lap_acc.append([float(time), float(f_acc[0].x[0]), float(f_acc[1].x[0]), float(f_acc[2].x[0]), float(row['Speed'])])

            if row_counter > 0:
                ang_acc_x, ang_acc_y, ang_acc_z = angular_acceleration(f_gyro, ang_vel_prev_x, ang_vel_prev_y, ang_vel_prev_z)
                roll += f_gyro[0].x[1][0]
                pitch += f_gyro[1].x[1][0]
                yaw = wrap_angle(yaw)

                point = (
                    Point('lap_times')
                    .tag("lap_time", 'last')
                    .field("last_time", last_time)
                    .time(timestamp)
                )
                points.append(point)

                point = (
                    Point('lap_times')
                    .tag('lap_time', 'best')
                    .field('best_time', best_time)
                    .time(timestamp)
                )
                points.append(point)

                point = (
                    Point('lap_times')
                    .tag('lap_time', 'best_lap_number')
                    .field('best_lap_number', best_lap_number)
                    .time(timestamp)
                )
                points.append(point)

                point = (
                    Point('lap_times')
                    .tag('lap_time', 'lap_number')
                    .field('lap_counter', lap_counter)
                    .time(timestamp)
                )
                points.append(point)

                # ang acc x
                point = (
                    Point('angular_acc')
                    .tag("axis", "x")
                    .field("ang_acc_x", ang_acc_x)
                    .time(timestamp)
                )
                points.append(point)
                
                # ang acc x
                point = (
                    Point('angular_acc')
                    .tag("axis", "y")
                    .field("ang_acc_y", ang_acc_y)
                    .time(timestamp)
                )
                points.append(point)
                
                # ang acc x
                point = (
                    Point('angular_acc')
                    .tag("axis", "z")
                    .field("ang_acc_z", ang_acc_z)
                    .time(timestamp)
                )
                points.append(point)

                # roll angle
                point = (
                    Point('angles')
                    .tag('axis', 'x')
                    .field('roll_angle', roll)
                    .time(timestamp)
                )
                points.append(point)

                # pitch angle
                point = (
                    Point('angles')
                    .tag('axis', 'y')
                    .field('pitch_angle', pitch)
                    .time(timestamp)
                )
                points.append(point)

                # yaw angle
                point = (
                    Point('angles')
                    .tag('axis', 'z')
                    .field('yaw_angle', yaw)
                    .time(timestamp)
                )
                points.append(point)


            vel_x += ((f_acc[0].x[1][0]) * 3.6)
            vel_y += ((f_acc[1].x[1][0]) * 3.6)
            vel_z += ((f_acc[2].x[1][0]) * 3.6)

            ang_vel_prev_x = f_gyro[0].x[0][0]
            ang_vel_prev_y = f_gyro[1].x[0][0]
            ang_vel_prev_z = f_gyro[2].x[0][0]

            lat_prev = f_gps[0].x[0][0]
            lon_prev = f_gps[1].x[0][0]

            #acc_prev_x = f_acc[0].x[0][0]
            #acc_prev_y = f_acc[1].x[0][0]
            #acc_prev_z = f_acc[1].x[0][0]

            # latitude and longitude
            point = (
                Point('gps')
                .tag('ID', 'gps_position')
                .field('latitude', float(f_gps[0].x[0][0]))
                .field('longitude', float(f_gps[1].x[0][0]))
                .time(timestamp)
            )
            points.append(point)

            # speed
            point = (
                Point('spd')
                .tag('Record', "velocity")
                .field('speed', float(row['Speed']))
                .time(timestamp)
                )
            points.append(point)
            
            # acc_x
            point = (
                Point('acc')
                .tag("axis", "x")
                .field("acc_x", float(f_acc[0].x[0][0]))
                .time(timestamp)
            )
            points.append(point)
            
            # acc_y
            point = (
                Point('acc')
                .tag("axis", "y")
                .field("acc_y", float(f_acc[1].x[0][0]))
                .time(timestamp)
            )
            points.append(point)
            
            # acc_z
            point = (
                Point('acc')
                .tag("axis", "z")
                .field("acc_z", float(f_acc[2].x[0][0]))
                .time(timestamp)
            )
            points.append(point)

                # gyro_x
            point = (
                Point('gyro')
                .tag("axis", "x")
                .field("gyro_x", float(f_gyro[0].x[0][0]))
                .time(timestamp)
            )
            points.append(point)
            
            # gyro_y
            point = (
                Point('gyro')
                .tag("axis", "y")
                .field("gyro_y", float(f_gyro[1].x[0][0]))
                .time(timestamp)
            )
            points.append(point)
            
            # gyro_z
            point = (
                Point('gyro')
                .tag("axis", "z")
                .field("gyro_z", float(f_gyro[2].x[0][0]))
                .time(timestamp)
            )
            points.append(point)

            

            # velocity x
            point = (
                Point('vel_acc')
                .tag('axis', 'x')
                .field('vel_x', vel_x)
                .time(timestamp)
            )
            points.append(point)

            # velocity y
            point = (
                Point('vel_acc')
                .tag('axis', 'y')
                .field('vel_y', vel_y)
                .time(timestamp)
            )
            points.append(point)

            # velocity z
            point = (
                Point('vel_acc')
                .tag('axis', 'z')
                .field('vel_z', vel_z)
                .time(timestamp)
            )
            points.append(point)

            row_counter += 1

            if row_counter % 300 == 0:
                write_api.write(bucket=bucket, org=org, record=points)
                points.clear()

        write_api.write(bucket=bucket, org=org, record=points)
        endTime = datetime.now()
        #with open('lap_53_no_steering_wheel.csv', 'w') as savu_file:
            #writer = csv.writer(savu_file)
            #writer.writerow(['seconds', 'acc_x', 'acc_y', 'acc_z', 'speed'])
            #writer.writerows(special_lap_acc)
        print(f'Calculated file number {file_counter} in {endTime - startTime}')



def wrap_angle(angle):
    while angle > 360:
        angle -= 360
    while angle < 0:
        angle+=360
    return angle
   
find_racebox(path)