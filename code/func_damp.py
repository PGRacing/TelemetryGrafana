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


def import_csv_damp(filepath, start_time, time_coefficients):
    # CSV column names as following:
    # timestamp,ID,delta
    # date like '2023-11-04'
    file = open(filepath, "r")
    csv_reader = csv.DictReader(file)
    line_count = 0
    points = []
    
    damp_data = DAMPKalman()
    #data_to_export = []
    startTime = datetime.datetime.now()
    previous_timestamp = None
    previous_csv_timestamp = None

    for row in csv_reader:
        # print(f'{row["timestamp"]}; {row["ID"]}; {row["delta"]}')

        #timestamp = start_time_add_timestamp(start_time, row["timestamp"])

        if line_count < 1:
            init_time = csv_timestamp_to_timedelta(row["timestamp"])
            first_timestamp = correct_init_time(init_time)
            timestamp = start_time + first_timestamp
        else:
            if len(time_coefficients) == 1:
                time_coefficient = 0.9489
            else:
                for i in range (1, len(time_coefficients)):
                    if csv_timestamp_to_timedelta(row["timestamp"]) >= csv_timestamp_to_timedelta(time_coefficients[i-1][0]) and \
                    csv_timestamp_to_timedelta(row["timestamp"]) < csv_timestamp_to_timedelta(time_coefficients[i][0]):
                        time_coefficient = time_coefficients[i-1][1]
                    elif csv_timestamp_to_timedelta(row["timestamp"]) <= csv_timestamp_to_timedelta(time_coefficients[0][0]):
                        time_coefficient = time_coefficients[0][1]
                    elif csv_timestamp_to_timedelta(row["timestamp"]) >= csv_timestamp_to_timedelta(time_coefficients[len(time_coefficients) - 1][0]):
                        time_coefficient = time_coefficients[len(time_coefficients) - 1][1]

            timestamp = correct_csv_timestamp(previous_csv_timestamp, row["timestamp"], previous_timestamp, time_coefficient)

        if line_count == 0:
            damp_data.init_kalman()
        data = filter_data(calc_wheel_position(row), row["ID"], damp_data)
        if row["ID"] != '6':
            position = damp_data.find_velocity_range(data[1])
            if position <= 0:
                point = (
                    Point('damp')
                    .tag("ID", f'{row["ID"]}')
                    .field("position_rebound", position)
                    .time(timestamp)
                )
                points.append(point)
            else:
                point = (
                    Point('damp')
                    .tag("ID", f'{row["ID"]}')
                    .field("position_bump", position)
                    .time(timestamp)
                )
                points.append(point)
        #minutes_total = datetime.datetime(year=2023, month=11, day=5, hour=9, minute=54)

        #if timestamp > start_of_lap:
        #    if row['ID'] == '6':
        #        time_s = timestamp - minutes_total
        #        time = time_s.total_seconds()
        #        data_to_export.append([time, data[0]])

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
            .field("velocity", data[1])
            .time(timestamp)
        )
        points.append(point)

        point = (
            Point('damp')
            .tag("ID", f'{row["ID"]}')
            .field("raw_delta", float(int(row["delta"])))
            #.time(timestamp)
        )
        # points.append(point)

        if line_count % 5000 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        line_count += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.datetime.now()
    file.close()
    print(f'DAMP: Imported {line_count} rows in {endTime - startTime}')
    #file = open('items.txt','w')
    #for i in range (0, len(data_to_export)):
    #    file.write(str(data_to_export[i][0]) + ' ' + str(data_to_export[i][1]) + ' ')
    #file.close()
    #return data_to_export


def setup_kalman_filter():
    global f
    # variance
    # for 0.00001 speed has too much noise
    # for 0.001 filter has too much delay  // in my opinion
    var = 0.014
    var_a = 0.5 * 530

    for i in range(5):
        f[i].x = np.array([[0.], [0.]])  # initial state (position and velocity)
        f[i].F = np.array([[1., 0.004], [0., 1.]])  # state transition matrix
        f[i].H = np.array([[1., 0.]])  # Measurement function
        f[i].P = np.array([[1000., 0.], [0., 1000.]])  # covariance matrix
        # proces noise and measurement noise needs to be fine-tuned
        f[i].R = np.array([[var]])  # measurement noise
        f[i].Q = Q_discrete_white_noise(dim=2, dt=0.004, var=var_a)  # process noise


def filter_data(data, ID, damp_data):
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
        damp_data.filter_damp(index, data)
        #f[index].predict()
        #f[index].update(data)
        #print(f'{float(f[index].x[0][0])}, {float(f[index].x[1][0])}')
        return float(damp_data.f[index].x[0][0]), float(damp_data.f[index].x[1][0])
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


class DAMPKalman:
    def __init__(self) -> None:
        self.f = list(range(5))
        self.var = 0.5 * 530
        self.var_damp = 0.014 
        self.timestep = 0.004 
        self.bump = [] 
        self.rebound = []
        self.damp_vel_percentage = []
        for i in range(10, 80, 10):
            self.bump.append([i, 0])
        for i in range(-70, 10, 10):
            self.rebound.append([i, 0])
            #self.damp_vel_percentage.append([i, 0])

    def init_kalman(self):
        for i in range(5):
            self.f[i] = KalmanFilter(dim_x=2, dim_z=1)
            self.f[i].x = np.array([[0.], 
                                    [0.]])  # initial state (position and velocity)
            self.f[i].F = np.array([[1., self.timestep], 
                                    [0., 1.]])  # state transition matrix
            self.f[i].H = np.array([[1., 0.]])  # Measurement function
            self.f[i].P = np.array([[10., 0.], 
                                    [0., 10.]])  # covariance matrix
            self.f[i].R = np.array([[self.var_damp]])  # measurement noise
            self.f[i].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var)  # process noise

    
    def filter_damp(self, index:int, value:float):
        self.f[index].predict()
        self.f[index].update(value)

    def find_velocity_range(self, velocity):
        # ugina się to prędkość na +
        # odgina to -
        if velocity < 0:
            for i in range(len(self.rebound)):
                if (velocity <= self.rebound[i][0]):
                    return self.rebound[i][0]
        else:
            for i in range(len(self.bump)):
                if (velocity <= self.bump[i][0]):
                    return self.bump[i][0]
            return self.bump[i][0]

    def calc_damp_values_percentage(self):
        number_of_records = 0
        for pair in self.bound:
            number_of_records += pair[1]
        

'''
path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/23-11-05 Pszczolki/damp/'       
if __name__ == '__main__':
    damp_data = DAMPKalman()
    temp_timestamp = datetime.datetime(year = 2023, month=11, day=5, hour=11)
    for item in os.listdir(path):
        full_path = os.path.join(path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            import_csv_damp(full_path, 0, damp_data)
            if item == 'DAMP0101-33.csv':
                damp_data.calc_damp_values_percentage()
                points = []
                for i in range(len(damp_data.damp_vel_percentage)):
                    point = (
                        Point('damp')
                        .tag("range", f'{damp_data.damp_vel_percentage[i][0]}%')
                        .field("percentage", float(damp_data.damp_vel_percentage[i][1]))
                        .time(temp_timestamp)
                    )
                    points.append(point)
                write_api.write(bucket=bucket, org=org, record=points)
'''