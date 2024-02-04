import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *
from damp_ang_to_pos import *

from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
import numpy as np

DAMPER_MIN_ANGLE = 0.0
DAMPER_MAX_ANGLE = 100.0
DAMPER_MID_ANGLE = (DAMPER_MAX_ANGLE + DAMPER_MIN_ANGLE) / 2.0


# DEG_TO_MM_FRONT = 1.221374046
# DEG_TO_MM_REAR = 1.070090958
# R_TO_DEG = 100.0
# 100R = 10mm

# linear interpolation
def lerp(a, b, alpha):
    return a + (alpha * (b - a))


R_TO_MM = 0.1
MAX_ADC_VALUE = 4095.0
REF_VAL_FL = 1080.0 / MAX_ADC_VALUE
REF_VAL_FR = 1740.0 / MAX_ADC_VALUE
REF_VAL_RL = 970.0 / MAX_ADC_VALUE
REF_VAL_RR = 1840.0 / MAX_ADC_VALUE

REF_ANGLE_FL = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_FL)
REF_ANGLE_FR = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_FR)
REF_ANGLE_RL = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_RL)
REF_ANGLE_RR = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_RR)

# 900R = 90deg
R_TO_DEG_SW = 0.1
REF_VAL_SW = 2380.0

f = list(KalmanFilter(dim_x=2, dim_z=1) for i in range(5))


# IDs
# 6  SW steering wheel
# 7  FL Front Left
# 8  FR Front Right
# 11 RL Rear Left
# 12 RR Rear Right

# 7  FL ugiecie zawieszenia - wzrost R
# 8  FR ugiecie zawieszenia - spadek R
# 11 RL ugiecie zawieszenia - wzrost R
# 12 RR ugiecie zawieszenia - spadek R

# 6  SW skret w lewo - wzrost R
# 6  SW skret w prawo - spadek R


def import_csv_damp(filepath, start_time):
    # CSV column names as following:
    # timestamp,ID,delta
    # date like '2023-11-04'
    file = open(filepath, "r")
    csv_reader = csv.DictReader(file)
    line_count = 0
    points = []
    startTime = datetime.datetime.now()
    previous_timestamp = None
    previous_csv_timestamp = None

    for row in csv_reader:
        # print(f'{row["timestamp"]}; {row["ID"]}; {row["delta"]}')
        if line_count < 1:
            init_time = csv_timestamp_to_timedelta(row["timestamp"])
            first_timestamp = correct_init_time(init_time)
            timestamp = start_time + first_timestamp
        else:
            timestamp = correct_csv_timestamp(previous_csv_timestamp, row["timestamp"], previous_timestamp)

        if line_count == 0:
            setup_kalman_filter()
        data = filter_data(calc_wheel_position(row), row["ID"])
        previous_timestamp = timestamp
        previous_csv_timestamp = row["timestamp"]
        point = (
            Point('damp')
            .tag("ID", f'{row["ID"]}')
            .field("angle", data[0])
            .time(timestamp)
        )
        points.append(point)

        # wheel travel in m/s
        point = (
            Point('damp')
            .tag("ID", f'{row["ID"]}')
            .field("velocity", data[1]/1000.0)
            .time(timestamp)
        )
        points.append(point)

        point = (
            Point('damp')
            .tag("ID", f'{row["ID"]}')
            .field("raw_delta", float(int(row["delta"])))
            .time(timestamp)
        )
        # points.append(point)

        if line_count % 5000 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        line_count += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.datetime.now()
    print(f'DAMP: Imported {line_count} rows in {endTime - startTime}')


def setup_kalman_filter():
    global f
    # variance
    # for 0.00001 speed has too much noise
    # for 0.001 filter has too much delay  // in my opinion
    var = 0.0001

    for i in range(5):
        f[i].x = np.array([[0.], [0.]])  # initial state (position and velocity)
        f[i].F = np.array([[1., 0.004], [0., 1.]])  # state transition matrix
        f[i].H = np.array([[1., 0.]])  # Measurement function
        f[i].P = np.array([[1000., 0.], [0., 1000.]])  # covariance matrix
        # proces noise and measurement noise needs to be fine-tuned
        f[i].R = np.array([[var ** 2]])  # measurement noise
        f[i].Q = Q_discrete_white_noise(dim=2, dt=0.004, var=var)  # process noise


def filter_data(data, ID):
    index = -1
    match int(ID):
        case 7:
            index = 0
        case 8:
            index = 1
        case 11:
            index = 2
        case 12:
            index = 3
        case 6:
            index = 4

    if index != -1:
        f[index].predict()
        f[index].update(data)
        #print(f'{float(f[index].x[0][0])}, {float(f[index].x[1][0])}')
        return float(f[index].x[0][0]), float(f[index].x[1][0])
    else:
        return data, 0.0


def calc_wheel_position(row):
    raw_value = float(int(row["delta"]))
    angle_abs = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, raw_value / 4095)
    angle = 0.0
    position = 0.0

    match int(row["ID"]):
        case 7:
            angle = -(angle_abs - REF_ANGLE_FL)
        case 8:
            angle = angle_abs - REF_ANGLE_FR
        case 11:
            angle = -(angle_abs - REF_ANGLE_RL)
        case 12:
            angle = (angle_abs - REF_ANGLE_RR)
        case 6:
            delta = (REF_VAL_SW - raw_value) * R_TO_DEG_SW

    # print(f'rawvalue = {raw_value}, angle_abs = {angle_abs}, angle = {angle}')

    if int(row["ID"]) != 6:
        if int(row["ID"]) == 7 or int(row["ID"]) == 8:
            try:
                damper_angle_to_pos_low, damper_angle_to_pos_high = find_closest_angles_front(angle)
            except IndexError:
                pass
        elif int(row["ID"]) == 11 or int(row["ID"]) == 12:
            try:
                damper_angle_to_pos_low, damper_angle_to_pos_high = find_closest_angles_back(angle)
            except IndexError:
                pass
        try:
            position = lerp(damper_angle_to_pos_low[0], damper_angle_to_pos_high[0],
                            (angle - damper_angle_to_pos_low[1]) / (
                                    damper_angle_to_pos_high[1] - damper_angle_to_pos_low[1]))
        except UnboundLocalError:
            pass
    else:
        position = delta

    return position
