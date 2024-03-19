import numpy as np
import math
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

GFORCE =  9.80665 # m/s2
# for racebox
TIMESTEP = 0.04 # s
# for our telemetry
#TIMESTEP = 0.004

VAR_ACC = 0.0000053744
VAR_GYRO = 0.0000053744
VAR_GPS = 0.000000000003664

def kalman_acc(f, acc_x, acc_y, acc_z, velocity_x, velocity_y, row_number):
    var_x = 0.5 * 7.58
    var_y = 0.5 * 16.4
    var_z = 0.5 * 11.5
    if row_number == 0:
        for i in range(3):
            f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                f[i].x = np.array([[acc_x], 
                                    [0.]])  # initial state (position and velocity)
            elif i == 1:
                f[i].x = np.array([[acc_y], 
                                    [0.]])
            else:
                f[i].x = np.array([[acc_z],
                                [GFORCE]])
            
            f[i].F = np.array([[1., 1/TIMESTEP], 
                                [0., 1.]])  # state transition matrix
            f[i].H = np.array([[1., 0.]])  # Measurement function
            f[i].P = np.array([[10., 0.], 
                                [0., 10.]])  # covariance matrix
            f[i].R = np.array([[VAR_ACC]])  # measurement noise
        f[0].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var_x)  # process noise
        f[1].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var_y)
        f[2].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var_z)


    f[0].predict()
    f[0].update(acc_x)
    f[1].predict()
    f[1].update(acc_y)
    f[2].predict()
    f[2].update(acc_z)

    return f

def kalman_gyro(f_gps, f_gyro, f_acc, gyro_x, gyro_y, gyro_z, row_number, x_prev, y_prev, yaw):
    var_x = 0.5 * 108.17
    var_y = 0.5 * 69.2
    var_z = 0.5 * 295.38
    var_fi = 0.7 * 8.022
    var_theta = 0.7 * 36.517
    var_psi = 0.7 * 134.03
    fi = math.degrees(math.atan2(f_acc[0].x[0][0], math.sqrt(f_acc[1].x[0][0]**2 + f_acc[2].x[0][0]**2)))
    theta = math.degrees(math.atan2(f_acc[1].x[0][0], math.sqrt(f_acc[0].x[0][0]**2 + f_acc[2].x[0][0]**2)))

    if row_number > 1\
        and abs(f_gyro[0].x[0][0]) < 1. \
        and abs(f_gyro[1].x[0][0]) < 1. \
        and abs(f_gyro[1].x[0][0]) < 1. :
        psi = yaw
    else:
        lat1 = math.radians(f_gps[0].x[0][0])
        lat2 = math.radians(y_prev)
        lon1 = math.radians(f_gps[1].x[0][0])
        lon2 = math.radians(x_prev)
        psi_r = math.atan2(math.sin(lon2 - lon1) * math.cos(lat2), math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))
        psi = math.degrees(psi_r)

    if row_number == 0:
        for i in range(3):
            f_gyro[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                f_gyro[i].x = np.array([[0.], 
                                        [fi]])  # initial state (position and velocity)
            elif i == 1:
                f_gyro[i].x = np.array([[0.], 
                                        [theta]])
            else:
                f_gyro[i].x = np.array([[0.],
                                        [psi]])
            
            f_gyro[i].F = np.array([[1., 1/TIMESTEP], 
                                    [0., 1.]])  # state transition matrix
            f_gyro[i].H = np.array([[1., 0.]])  # Measurement function
            f_gyro[i].P = np.array([[0.0004, 0.], 
                                    [0., 0.04]])  # covariance matrix
        f_gyro[0].R = np.array([[VAR_GYRO]])
        f_gyro[1].R = np.array([[VAR_GYRO]])
        f_gyro[2].R = np.array([[VAR_GYRO]])  # measurement noise
        f_gyro[0].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var_x)  # process noise
        f_gyro[1].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var_y)
        f_gyro[2].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var_z)


    f_gyro[0].predict()
    f_gyro[0].update(gyro_x)
    f_gyro[1].predict()
    f_gyro[1].update(gyro_y)
    f_gyro[2].predict()
    f_gyro[2].update(gyro_z)

    return f_gyro, psi


def kalman_gps(f, lat, lon, row_number):
    signal_loss = False
    var = 0.5 * 13.08
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
            f[i].R = np.array([[VAR_GPS]])  # measurement noise
            f[i].Q = Q_discrete_white_noise(dim=2, dt=TIMESTEP, var=var)  # process noise

    if lat == '':
        lat = 0.0
        signal_loss = True
    elif lon == '':
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
    delta_x = float(f_gyro[0].x[0][0]) - prev_x
    delta_y = float(f_gyro[1].x[0][0]) - prev_y
    delta_z = float(f_gyro[2].x[0][0]) - prev_z

    ang_acc_x = delta_x/TIMESTEP
    ang_acc_y = delta_y/TIMESTEP
    ang_acc_z = delta_z/TIMESTEP

    return ang_acc_x, ang_acc_y, ang_acc_z


def velocity_acc(f_acc, acc_prev_x, acc_prev_y, acc_prev_z):
    area_x = (((f_acc[0].x[0][0] + acc_prev_x) / 2.) * TIMESTEP) * 0.01/(1/3600)
    area_y = (((f_acc[1].x[0][0] + acc_prev_y) / 2.) * TIMESTEP) * 0.01/(1/3600)
    area_z = (((f_acc[2].x[0][0] + acc_prev_z) / 2.) * TIMESTEP) * 0.01/(1/3600)

    return area_x, area_y, area_z


def kalman_temp(f, engine_in, engine_out, lr_in, lr_out, rr_in, rr_out, row_number):
    #var = 0.5 * 4.97 
    #var =  0.5 * 0.109
    #var = 0.5 * 0.0259
    var = 0.5 * 0.0003
    #var_cooling = 0.003191606129303
    var_cooling = 1.
    timestep = 1.004987702853438
    if row_number == 1:
        for i in range(6):
            f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                f[i].x = np.array([[engine_in], 
                                    [0.]])  # initial state (position and velocity)
            elif i == 1:
                f[i].x = np.array([[engine_out], 
                                    [0.]])
            elif i == 2:
                f[i].x = np.array([[lr_in],
                                    [0.]])
            elif i == 3:
                f[i].x = np.array([[lr_out], 
                                    [0.]])
            elif i == 4:
                f[i].x = np.array([[rr_in], 
                                    [0.]])
            elif i == 5:
                f[i].x = np.array([[rr_out], 
                                    [0.]])
            
            f[i].F = np.array([[1., timestep], 
                                [0., 1.]])  # state transition matrix
            f[i].H = np.array([[1., 0.]])  # Measurement function
            f[i].P = np.array([[10., 0.], 
                                [0., 10.]])  # covariance matrix
            f[i].R = np.array([[var_cooling]])  # measurement noise
            f[i].Q = Q_discrete_white_noise(dim=2, dt=timestep, var=var)  # process noise

    for i in range(6):
        f[i].predict()
    f[0].update(engine_in)
    f[1].update(engine_out)
    f[2].update(lr_in)
    f[3].update(lr_out)
    f[4].update(rr_in)
    f[5].update(rr_out)

    return f


