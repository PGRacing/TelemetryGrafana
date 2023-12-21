import csv
import datetime
import os

from code.func_damp import calc_wheel_position
from code.main import paths
from code.utils_timestamp import csv_timestamp_to_datetime
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
import matplotlib.pyplot as plt
import numpy as np
import time

file_to_test = "DAMP0101-12.csv"
low_pass_filter_alpha_50Hz = 0.55
low_pass_filter_alpha_25Hz = 0.38


def test_import_csv_damp():
    for path in paths:
        if os.path.exists(path):
            # for i in range(1,20):
            # threading.Thread(target=read_file, args=(path + "DAMP0101-" + str(i) + ".csv",)).start()
            # read_file(path + "DAMP0101-" + str(i) + ".csv")
            read_file(path + file_to_test)
            break


def low_pass_filter(value, last_value, alpha):
    return alpha * value + (1 - alpha) * last_value


def read_file(file_path):
    with (open(file_path, "r") as file):
        csv_reader = csv.DictReader(file)
        wheels_positions = []
        wheels_timestamps = []
        max_speed = 0.0
        max_speed_raw = 0.0
        max_speed_kalman = 0.0
        for i in range(8):
            wheels_positions.append([0.0])
            wheels_timestamps.append([])

        f = list(range(4))
        # variance
        # for 0.00001 speed has to much noise
        # for 0.001 filter has to much delay  // in my opinion

        var = 0.0001
        for i in range(4):
            f[i] = KalmanFilter(dim_x=2, dim_z=1)
            f[i].x = np.array([[0.], [0.]])  # initial state (position and velocity)
            f[i].F = np.array([[1., 0.004], [0., 1.]])  # state transition matrix
            f[i].H = np.array([[1., 0.]])  # Measurement function
            f[i].P = np.array([[1000., 0.], [1000., 0.]])  # covariance matrix
            # proces noise and measurement noise needs to be fine tuned
            # measurement noise smaller -> kalman filter follows raw data more closely
            # process noise bigger -> kalman filter follows raw data more closely
            # but this need to be checked
            f[i].R = np.array([[var**2]])  # measurement noise
            f[i].Q = Q_discrete_white_noise(dim=2, dt=0.004, var=var)  # process noise

        for row in csv_reader:
            value = calc_wheel_position(row)
            index = 0
            match int(row["ID"]):
                case 7:
                    index = 0
                case 8:
                    index = 1
                case 11:
                    index = 2
                case 12:
                    index = 3
                case 6:
                    continue
            #if index == 0:
            f[index].predict()
            f[index].update(value)
            # print(f[index].x)

            # wheels_positions[index].append(value)

            wheels_timestamps[index].append(
                csv_timestamp_to_datetime(datetime.datetime(year=2023, month=11, day=5), row["timestamp"]))
            wheels_positions[index].append(float((f[index].x[0][0])))
            wheels_positions[index + 4].append(float((f[index].x[1][0])))
                #wheels_positions[index+1].append(low_pass_filter(value, wheels_positions[index+1][-1], low_pass_filter_alpha_50Hz))
                #wheels_positions[index+1].append(value)

               # if f[index].x[1][0] > max_speed_kalman:
               #     max_speed_kalman = f[index].x[1][0]
               #     print(f"New max speed kalman: {max_speed_kalman}")

               # if len(wheels_positions[index]) > 1 and (
               #         wheels_positions[index][-1] - wheels_positions[index][-2]) / 0.004 > max_speed:
               #     max_speed = (wheels_positions[index][-1] - wheels_positions[index][-2]) / 0.004
               #     print(f"New max speed: {max_speed}")
               # if len(wheels_positions[index+1]) > 1 and (
               #         wheels_positions[index+1][-1] - wheels_positions[index+1][-2]) / 0.004 > max_speed_raw:
               #     max_speed_raw = (wheels_positions[index+1][-1] - wheels_positions[index+1][-2]) / 0.004
                #    print(f"New max speed raw: {max_speed_raw}")

        for i in range(8):
            wheels_positions[i].pop(0)
        # plt.plot(wheels_timestamps[0], wheels_positions[0], label="no filter")
        #plt.plot(wheels_timestamps[1], wheels_positions[1], label="low pass 50 Hz")
        # plt.plot(wheels_timestamps[2], wheels_positions[2], label="low pass 25 Hz")
        # plt.plot(wheels_timestamps[3], wheels_positions[3], label="kalman")

        plt.plot(wheels_timestamps[0], wheels_positions[0], label="FL")
        plt.plot(wheels_timestamps[1], wheels_positions[1], label="FR")
        plt.plot(wheels_timestamps[2], wheels_positions[2], label="RL")
        plt.plot(wheels_timestamps[3], wheels_positions[3], label="RR")

        #plt.plot(wheels_timestamps[0], wheels_positions[4], label="FL Speed")
        plt.legend(title='Wheel:')
        plt.show()


if __name__ == "__main__":
    print("Damper test")
    test_import_csv_damp()
