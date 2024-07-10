import csv
import struct
from datetime import datetime
from conf_influxdb import *
from kalman_filters import *
from utils_timestamp import *

def import_csv_imu(filepath, start_time, f_acc, f_gyro):
    # CSV column names as following:
    # timestamp,gyro_x,gyro_y,gyro_z,acc_x,acc_y,acc_z
    # date like '2023-11-04'
    file = open(filepath, "r")
    csv_reader = csv.DictReader(file)
    line_count = 0
    points = []
    previous_timestamp = None
    previous_csv_timestamp = None
    startTime = datetime.datetime.now()


    # TODO not initializing those values in each file
    ang_vel_prev_x = 0.
    ang_vel_prev_y = 0.
    ang_vel_prev_z = 0.
    
    roll = 0.
    pitch = 0.
    yaw = 0.

    vel_x = 0.
    vel_y = 0.
    vel_z = 0.

    lat_prev = 0.
    lon_prev = 0.

    acc_prev_x = 0.
    acc_prev_y = 0.
    acc_prev_z = 0.



    for row in csv_reader:
        #print(f'{row["timestamp"]}; {row["gyro_x"]}; {row["gyro_y"]}; {row["gyro_z"]}; {row["acc_x"]}; {row["acc_y"]}; {row["acc_z"]};')
        if line_count < 1:
            init_time = csv_timestamp_to_timedelta(row["timestamp"])
            first_timestamp = correct_init_time(init_time)
            timestamp = start_time + first_timestamp
        else:
            timestamp = correct_csv_timestamp(previous_csv_timestamp, row["timestamp"], previous_timestamp)

        #f_acc = kalman_acc(f_acc, )
        previous_timestamp = timestamp
        previous_csv_timestamp = row["timestamp"]
        # gyro_x
        point = (
            Point('gyro')
            .tag("axis", "x")
            .field("gyro_x", float(row["gyro_x"]))
            .time(timestamp)
        )
        points.append(point)
        
        # gyro_y
        point = (
            Point('gyro')
            .tag("axis", "y")
            .field("gyro_y", float(row["gyro_y"]))
            .time(timestamp)
        )
        points.append(point)
        
        # gyro_z
        point = (
            Point('gyro')
            .tag("axis", "z")
            .field("gyro_z", float(row["gyro_z"]))
            .time(timestamp)
        )
        points.append(point)
        
        # acc_x
        point = (
            Point('acc')
            .tag("axis", "x")
            .field("acc_x", float(row["acc_x"]))
            .time(timestamp)
        )
        points.append(point)
        
        # acc_y
        point = (
            Point('acc')
            .tag("axis", "y")
            .field("acc_y", float(row["acc_y"]))
            .time(timestamp)
        )
        points.append(point)
        
        # acc_z
        point = (
            Point('acc')
            .tag("axis", "z")
            .field("acc_z", float(row["acc_z"]))
            .time(timestamp)
        )
        points.append(point)
        
        if line_count % 1000 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        line_count += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.datetime.now()
    file.close()
    print(f'IMU: Imported {line_count} rows in {endTime - startTime}')

    return f_acc, f_gyro


'''
TODO: Calculate variance for imu and gps
'''

def acc_data_live(queue, timestamp, f_acc, lap_counter, lap_diff):
    acc_multiplier = 128.
    data = bytearray()

    for i in range(3):
        data.extend([queue.get()])
    acc_x, acc_y, acc_z = struct.upack("<HHH", data)

    if acc_x:
        acc_x /= acc_multiplier
        acc_y /= acc_multiplier
        acc_z /= acc_multiplier

        f_acc.filter_acc(acc_x, acc_y, acc_z, False)
        new_lap_forces = f_acc.curve_detector(lap_counter, lap_diff)

    else:
        f_acc.filter_acc(acc_x, acc_y, acc_z, True)

    data_to_send = {
        "acc_x": f_acc[0].x[0][0],
        "acc_y": f_acc[1].x[0][0],
        "acc_z": f_acc[2].x[0][0]
    }

    if new_lap_forces:
        data_to_send.update(new_lap_forces)

    return data_to_send

def gyro_data_live(queue, f_gyro):
    gyro_multiplier = 128.
    data = bytearray()

    for i in range(3):
        data.extend([queue.get()])
    gyro_x, gyro_y, gyro_z = struct.unpack("<HHH", data)
    if gyro_x:
        gyro_x /= gyro_multiplier
        gyro_y /= gyro_multiplier
        gyro_z /= gyro_multiplier

        f_gyro.filter_gyro(gyro_x, gyro_y, gyro_z, False)

    else:
        f_gyro.filter_gyro(gyro_x, gyro_y, gyro_z, True)

    data_to_send = {"gyro_x": f_gyro.f[0].x[0][0],
                    "gyro_y": f_gyro.f[1].x[0][0],
                    "gyro_z": f_gyro.f[2].x[0][0]}
    return data_to_send