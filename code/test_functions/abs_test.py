import csv
import os

from code.main import paths
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from code.test_functions.filters import low_pass_filter, fir_filter, get_alpha
import matplotlib.pyplot as plt
import numpy as np

file_to_test = "ABS0101-12.csv"
low_pass_filter_alpha_50Hz = get_alpha(0.004, 50)
low_pass_filter_alpha_25Hz = get_alpha(0.004, 25)
low_pass_filter_alpha_5Hz = get_alpha(0.004, 5)
low_pass_filter_alpha_4Hz = get_alpha(0.004, 4)
low_pass_filter_alpha_2Hz = get_alpha(0.004, 2)


def test_import_csv_abs():
    for path in paths:
        if os.path.exists(path):
            # for i in range(1,20):
            # threading.Thread(target=read_file, args=(path + "DAMP0101-" + str(i) + ".csv",)).start()
            # read_file(path + "DAMP0101-" + str(i) + ".csv")
            read_file(path + file_to_test)
            break


def read_file(file_path):
    with (open(file_path, "r") as file):
        csv_reader = csv.DictReader(file)
        wheels_speed = []
        wheels_timestamps = []
        sample_num = 6
        coeff = 1 / sample_num
        coeff_array = [coeff for _ in range(sample_num)]
        sample_num2 = 3
        coeff2 = 1 / sample_num2
        coeff_array2 = [coeff2 for _ in range(sample_num2)]

        for i in range(8):
            wheels_speed.append([0.0])
            wheels_timestamps.append([])

        f = list(range(4))
        # variance
        # for 0.00001 speed has too much noise
        # for 0.001 filter has too much delay  // in my opinion

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
            f[i].R = np.array([[var ** 2]])  # measurement noise
            f[i].Q = Q_discrete_white_noise(dim=2, dt=0.004, var=var)  # process noise

        for row in csv_reader:
            value = float(row["speed"]) * 2.0
            index = 0
            match int(row["ID"]):
                case 4:
                    index = 0
                case 5:
                    continue
                    index = 1
            # if index == 0:
            # f[index].predict()
            # f[index].update(value)
            # print(f[index].x)

            wheels_speed[index].append(value)

            wheels_timestamps[index].append(float(row["timestamp"]))
            wheels_speed[index + 1].append(
                low_pass_filter(value, wheels_speed[index + 1][-1], low_pass_filter_alpha_4Hz))

            wheels_speed[index + 2].append(
                fir_filter(value, wheels_speed[index + 2][-min(len(wheels_speed[index + 2]) - 2, sample_num - 1):],
                           coeff_array))

            wheels_speed[index + 3].append(
                low_pass_filter(value, fir_filter(value, wheels_speed[index + 3][
                                                         -min(len(wheels_speed[index + 3]) - 2, sample_num2 - 1):],
                                                  coeff_array2), low_pass_filter_alpha_5Hz))

        for i in range(8):
            wheels_speed[i].pop(0)
        # plt.plot(wheels_timestamps[0], wheels_positions[0], label="no filter")
        # plt.plot(wheels_timestamps[1], wheels_positions[1], label="low pass 50 Hz")
        # plt.plot(wheels_timestamps[2], wheels_positions[2], label="low pass 25 Hz")
        # plt.plot(wheels_timestamps[3], wheels_positions[3], label="kalman")

        plt.plot(wheels_timestamps[0], wheels_speed[0], label="FL")
        # plt.plot(wheels_timestamps[1], wheels_speed[1], label="FR")

        plt.plot(wheels_timestamps[0], wheels_speed[1], label="FL iir")
        plt.plot(wheels_timestamps[0], wheels_speed[2], label="FL firr")
       # plt.plot(wheels_timestamps[0], wheels_speed[3], label="FL double filter")
        # plt.plot(wheels_timestamps[1], wheels_speed[3], label="FR")

        # plt.plot(wheels_timestamps[0], wheels_positions[4], label="FL Speed")
        plt.legend(title='Wheel:')
        plt.show()


if __name__ == "__main__":
    print("ABS test")
    test_import_csv_abs()
