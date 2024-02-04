import numpy as np
import math
from datetime import datetime
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

GFORCE =  9.80665 # m/s2
# for racebox
#TIMESTEP = 0.04 # s
# for our telemetry
TIMESTEP = 0.004

def kalman_acc(f, acc_x, acc_y, acc_z, velocity_x, velocity_y, row_number):
    var = 0.0001
    if row_number == 0:
        for i in range(3):
            f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                f[i].x = np.array([[acc_x], 
                                    [velocity_x]])  # initial state (position and velocity)
            elif i == 1:
                f[i].x = np.array([[acc_y], 
                                    [velocity_y]])
            else:
                f[i].x = np.array([[acc_z],
                                [GFORCE]])
            
            f[i].F = np.array([[1., 1/TIMESTEP], 
                                [0., 1.]])  # state transition matrix
            f[i].H = np.array([[1., 0.]])  # Measurement function
            f[i].P = np.array([[10., 0.], 
                                [0., 10.]])  # covariance matrix
            f[i].R = np.array([[var]])  # measurement noise
            f[i].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var)  # process noise


    f[0].predict()
    f[0].update(acc_x)
    f[1].predict()
    f[1].update(acc_y)
    f[2].predict()
    f[2].update(acc_z)

    return f

def kalman_gyro(f_gyro, f_acc, gyro_x, gyro_y, gyro_z, row_number):
    var = 0.0001
    alfa = math.degrees(math.atan(f_acc[2].x[0][0]/f_acc[0].x[0][0]))
    if row_number == 0:
        for i in range(3):
            f_gyro[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                f_gyro[i].x = np.array([[alfa], 
                                        [0.]])  # initial state (position and velocity)
            elif i == 1:
                f_gyro[i].x = np.array([[alfa], 
                                        [0.]])
            else:
                f_gyro[i].x = np.array([[alfa],
                                        [0.]])
            
            f_gyro[i].F = np.array([[1., TIMESTEP], 
                                [0., 1.]])  # state transition matrix
            f_gyro[i].H = np.array([[1., 0.]])  # Measurement function
            f_gyro[i].P = np.array([[10., 0.], 
                                [0., 10.]])  # covariance matrix
            f_gyro[i].R = np.array([[var]])  # measurement noise
            f_gyro[i].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var)  # process noise


    f_gyro[0].predict()
    f_gyro[0].update(gyro_x)
    f_gyro[1].predict()
    f_gyro[1].update(gyro_y)
    f_gyro[2].predict()
    f_gyro[2].update(gyro_z)

    return f_gyro


def kalman_gps(f, lat, lon, row_number):
    signal_loss = False
    var = 0.0000001
    if row_number == 0:
        for i in range(2):
            f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                f[i].x = np.array([[lat], 
                                    [0.]])  # initial state (position and velocity)
            elif i == 1:
                f[i].x = np.array([[lon], 
                                    [0.]])
            
            f[i].F = np.array([[1., TIMESTEP], 
                                [0., 1.]])  # state transition matrix
            f[i].H = np.array([[1., 0.]])  # Measurement function
            f[i].P = np.array([[10., 0.], 
                                [0., 10.]])  # covariance matrix
            f[i].R = np.array([[var]])  # measurement noise
            f[i].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var)  # process noise

    if lat == '':
        lat = 0.0
        signal_loss = True
    elif lon != '':
        lon = 0.0
        signal_loss = True
    
    if signal_loss == True:
        f[0].predict()
        f[1].predict()
    else:
        f[0].predict()
        f[0].update(lat)
        f[1].predict()
        f[1].update(lon)


    return f

def angular_acceleration(f_gyro, prev_x, prev_y, prev_z):
    delta_x = float(f_gyro[0].x[1][0]) - prev_x
    delta_y = float(f_gyro[1].x[1][0]) - prev_y
    delta_z = float(f_gyro[2].x[1][0]) - prev_z

    ang_acc_x = delta_x/TIMESTEP
    ang_acc_y = delta_y/TIMESTEP
    ang_acc_z = delta_z/TIMESTEP

    return ang_acc_x, ang_acc_y, ang_acc_z


def calculate_angles(f_gyro, gyro_x_prev, gyro_y_prev, gyro_z_prev):
    #roll_angle = math.degrees(math.atan2(f_acc[1].x[0][0], math.sqrt((f_acc[0].x[0][0])**2 + (f_acc[2].x[0][0])**2)))
    #pitch_angle = math.degrees(math.atan2(-f_acc[0].x[0][0], math.sqrt((f_acc[1].x[0][0])**2 + (f_acc[2].x[0][0])**2)))
    #yaw_angle = yaw_previous + (f_gyro[2].x[1][0] * timestep)
    #return roll_angle, pitch_angle, yaw_angle
    roll = ((f_gyro[0].x[1][0] + gyro_x_prev) / 2.) * TIMESTEP
    pitch = ((f_gyro[1].x[1][0] + gyro_y_prev) / 2.) * TIMESTEP
    yaw = ((f_gyro[2].x[1][0] + gyro_z_prev) / 2.) * TIMESTEP

    return roll, pitch, yaw

def velocity_acc(f_acc, acc_prev_x, acc_prev_y, acc_prev_z):
    area_x = (((f_acc[0].x[0][0] + acc_prev_x) / 2.) * TIMESTEP) * 0.01/(1/3600)
    area_y = (((f_acc[1].x[0][0] + acc_prev_y) / 2.) * TIMESTEP) * 0.01/(1/3600)
    area_z = (((f_acc[2].x[0][0] + acc_prev_z) / 2.) * TIMESTEP) * 0.01/(1/3600)

    return area_x, area_y, area_z



