import numpy as np
import csv
import math
from conf_influxdb import *
from kalman_filters import *
from data_filtration import *
from variances import *
from lap_timer import *
from time_loss import *
from datetime import datetime
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise


path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-03 Pszczolki/racebox/'

GFORCE =  9.80665 # m/s2
TIMESTEP = 0.04 # s
file_counter = 0
lap_counter = 0
last_time = 0.
best_lap_number = 0
best_time = 0.
var_gyro = 0.
var_acc = 0.
total_km = 0.

special_lap = []
laps = []

# to be set every track change
approx_lon = 18.712
approx_lat = 54.178
lat_prev = 54.1784441
lon_prev = 18.7133100

conv_rate_lon = math.degrees(math.cos(math.radians(approx_lat))) * (40075000/360) # deg to met
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
    global total_km
    global laps
    
    with open(filefullpath, 'r') as file:
        lap_timer = LapTimer()
        gps_data = GPSKalman()
        acc_data = ACCKalman()
        gyro_data = GYROKalman()
        #time_loss = TimeLoss()
        #csvreader_object = csv.reader(file)
        #for i in range (1, 13):
            #ext(csvreader_object)
        data = csv.DictReader(file)
        points = []
        startTime = datetime.now()
        row_counter = 0
        lap_diff = 0
        inner_lap_counter = 0
        lap_duration_time = 0.

        #f_gps = list(range(3))
        #f_acc = list(range(3))
        #f_gyro = list(range(3))
        
        ang_vel_prev_x = 0.
        ang_vel_prev_y = 0.
        ang_vel_prev_z = 0.
        
        roll = 0.
        pitch = 0.
        yaw = 0.

        vel_x = 0.
        vel_y = 0.
        vel_z = 0.


        #gps_data.init_kalman()
        acc_data.init_kalman()
        gyro_data.init_kalman()


        for row in data:
            signal_loss_gps = False
            signal_loss_acc = False
            signal_loss_gyro = False
            gyro_x = float(row['GyroX'])
            gyro_y = float(row['GyroY'])
            gyro_z = float(row['GyroZ'])

            GForceX = float(row['GForceX']) * GFORCE 
            GForceY = float(row['GForceY']) * GFORCE 
            GForceZ = float(row['GForceZ']) * GFORCE

            timestamp = row['Time']

            if not row['Latitude'] or not row['Longitude']:
                signal_loss_gps = True
            gps_data.filter_gps(float(row['Latitude']), float(row['Longitude']), signal_loss_gps)

            if row_counter == 0:
                lap_timer.init_position(x=gps_data.f[1].x[0][0], y=gps_data.f[0].x[0][0], time=timestamp)
            else:
                last_time, lap_diff, inner_lap_counter, lap_duration_time = lap_timer.check(x=gps_data.f[1].x[0][0], y=gps_data.f[0].x[0][0], timestamp=timestamp)
                #prev_lap = lap_counter
                lap_counter += lap_diff
                #if prev_lap == 56 and lap_counter == 4 and lap_diff != 0:
                    #print('maybe something here')
            if (last_time < best_time and inner_lap_counter != 0) or lap_counter == 1:
                    best_time = last_time
                    best_lap_number = lap_counter

            gps_data.avg_speed_per_lap(lap_counter, lap_diff, float(row['Speed']), timestamp, points)

            if not row['GForceX'] or not row['GForceY'] or not row['GForceZ']:
                signal_loss_acc = True
            acc_data.filter_acc(GForceX, GForceY, GForceZ, signal_loss_acc)
            acc_data.curve_detector(lap_counter,lap_diff, timestamp, points)

            if not gyro_x or not gyro_y or not gyro_z:
                signal_loss_gyro = True
            gyro_data.filter_gyro(gyro_x, gyro_y, gyro_z, signal_loss_gyro)
            yaw = gyro_data.calc_and_wrap_yaw(lon_prev, lat_prev)
            roll += gyro_data.f[0].x[1][0]
            pitch += gyro_data.f[1].x[1][0]

            
            '''
            f_gps = kalman_gps(f_gps, float(row['Latitude']), float(row['Longitude']), row_counter)
            
            f_acc = kalman_acc(f_acc, GForceX, GForceY, GForceZ, (f_gps[1].x[1][0] * conv_rate_lon), (f_gps[0].x[1][0] * conv_rate_lat), row_counter)
            f_gyro, yaw = kalman_gyro(f_gps, f_gyro, f_acc, gyro_x, gyro_y, gyro_z, row_counter, lon_prev, lat_prev, yaw)
            '''
            
            
            #loss = time_loss.calucate_gain_loss(gps_data.f[1].x[0][0], gps_data.f[0].x[0][0], lap_duration_time)

            #if lap_counter == 2:
                #time = row['Time'][17:23]
                #special_lap_acc.append([float(time), float(f_acc[0].x[0]), float(f_acc[1].x[0]), float(f_acc[2].x[0]), float(row['Speed'])])
                #special_lap.append([float(f_gps[1].x[0][0]), float(f_gps[0].x[0][0]), lap_duration_time])
            '''
            if row_counter > 0:
                
                roll += f_gyro[0].x[1][0]
                pitch += f_gyro[1].x[1][0]
                yaw = wrap_angle(yaw)
            '''
            ang_acc_x, ang_acc_y, ang_acc_z = angular_acceleration(gyro_data, ang_vel_prev_x, ang_vel_prev_y, ang_vel_prev_z)
            total_km += calc_kilometers_driven(math.radians(gps_data.f[0].x[0][0]), math.radians(gps_data.f[1].x[0][0]), math.radians(lat_prev), math.radians(lon_prev))
            
            point = (
                Point('gps')
                .tag("ID", 'total2')
                .field("km_driven", total_km)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('lap_times')
                .tag("lap_time", 'loss')
                #.field("time_loss2", loss)
                .time(timestamp)
            )
            #points.append(point)

            point = (
                Point('lap_times')
                .tag("lap", 'duration')
                #.field("lap_duration", lap_duration_time)
                .time(timestamp)
            )
            points.append(point)

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
            

            vel_x += ((acc_data.f[0].x[1][0]) * 3.6)
            vel_y += ((acc_data.f[1].x[1][0]) * 3.6)
            vel_z += ((acc_data.f[2].x[1][0]) * 3.6)

            ang_vel_prev_x = gyro_data.f[0].x[0][0]
            ang_vel_prev_y = gyro_data.f[1].x[0][0]
            ang_vel_prev_z = gyro_data.f[2].x[0][0]

            lat_prev = gps_data.f[0].x[0][0]
            lon_prev = gps_data.f[1].x[0][0]

            # latitude and longitude
            point = (
                Point('gps')
                .tag('ID', 'gps_position')
                #.field('latitude', float(f_gps[0].x[0][0]))
                #.field('longitude', float(f_gps[1].x[0][0]))
                .field('latitude', gps_data.f[0].x[0][0])
                .field('longitude', gps_data.f[1].x[0][0])
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
                .field("acc_x", acc_data.f[0].x[0][0])
                .time(timestamp)
            )
            points.append(point)
            
            # acc_y
            point = (
                Point('acc')
                .tag("axis", "y")
                .field("acc_y", acc_data.f[1].x[0][0])
                .time(timestamp)
            )
            points.append(point)
            
            # acc_z
            point = (
                Point('acc')
                .tag("axis", "z")
                .field("acc_z", acc_data.f[2].x[0][0])
                .time(timestamp)
            )
            points.append(point)
            
                # gyro_x
            point = (
                Point('gyro')
                .tag("axis", "x")
                .field("gyro_x", gyro_data.f[0].x[0][0])
                .time(timestamp)
            )
            points.append(point)
            
            # gyro_y
            point = (
                Point('gyro')
                .tag("axis", "y")
                .field("gyro_y", gyro_data.f[1].x[0][0])
                .time(timestamp)
            )
            points.append(point)
            
            # gyro_z
            point = (
                Point('gyro')
                .tag("axis", "z")
                .field("gyro_z", gyro_data.f[2].x[0][0])
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

        #mean_gforce = acc_data.calc_avg_gforce()
        #point = (
        #    Point('force')
        #    .tag('number', f'{file_counter}')
        #    .field('mean_force', mean_gforce)
        #    .time(timestamp)
        #)
        #points.append(point)


        write_api.write(bucket=bucket, org=org, record=points)
        endTime = datetime.now()
        #with open('Pszczolki_fastest_long_lap.csv', 'w') as savu_file:
            #writer = csv.writer(savu_file)
            #writer.writerow(['lon', 'lat', 'time'])
            #writer.writerows(special_lap)
        print(f'Calculated file number {file_counter} in {endTime - startTime}')



def wrap_angle(angle):
    while angle > 360:
        angle -= 360
    while angle < 0:
        angle+=360
    return angle


def calc_kilometers_driven(lat_current, lon_current, lat_prev, lon_prev):
    radius_earth_km = 6371.0
    delta_lat = lat_current - lat_prev
    delta_lon = lon_current - lon_prev
    a = math.sin(delta_lat / 2)**2 + math.cos(lat_prev) * math.cos(lat_current) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = radius_earth_km * c
    return distance_km

if __name__ == '__main__':
    find_racebox(path)