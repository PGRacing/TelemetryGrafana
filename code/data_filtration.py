import math
import numpy as np
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from conf_influxdb import *

class GPSKalman:
    def __init__(self) -> None:
        self.f = list(range(2))
        self.var = 0.5 * 13.08
        self.var_gps = 0.000000000003664 # racebox gps
        self.timestep = 0.04 # in racebox
        self.speed_one_lap_container = []

    def init_kalman(self, lat, lon):
        for i in range(2):
            self.f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                self.f[i].x = np.array([[lat], 
                                        [0.]])  # initial state (position and velocity)
            elif i == 1:
                self.f[i].x = np.array([[lon], 
                                        [0.]])
            
            self.f[i].F = np.array([[1., self.timestep], 
                                    [0., 1.]])  # state transition matrix
            self.f[i].H = np.array([[1., 0.]])  # Measurement function
            self.f[i].P = np.array([[10., 0.], 
                                    [0., 10.]])  # covariance matrix
            self.f[i].R = np.array([[self.var_gps]])  # measurement noise
            self.f[i].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var)  # process noise
        
    
    def filter_gps(self, lat:float, lon:float, signal_loss:bool):
        if type(self.f[0]) == int:
            self.init_kalman(lat, lon)
        for i in range(2):
            self.f[i].predict()
        if not signal_loss:
            self.f[0].update(lat)
            self.f[1].update(lon)

    def avg_speed_per_lap(self, lap_number, lap_diff, speed, timestamp, points):
        if lap_diff == 1:
            if(len(self.speed_one_lap_container)>0):
                mean_speed = mean(self.speed_one_lap_container)
                self.speed_one_lap_container.clear()
                point = (
                    Point('spd')
                    .tag('avg', 'speed')
                    .field("lap_number", lap_number)
                    .field("mean_speed", mean_speed)
                    .time(timestamp)
                )
                points.append(point)

        self.speed_one_lap_container.append(speed)

    
class ACCKalman:
    def __init__(self) -> None:
        self.f = list(range(3))
        self.var_x = 0.5 * 7.58
        self.var_y = 0.5 * 16.4
        self.var_z = 0.5 * 11.5
        self.var_acc = 0.0000053744 # racebox acc
        self.timestep = 0.04 # in racebox
        self.gforce = 9.80665
        self.laps_send = 0
        self.one_lap_container_y = []
        self.one_lap_container_x = []
        self.curve_gforces = []

    def init_kalman(self):
        for i in range(3):
            for i in range(3):
                self.f[i] = KalmanFilter(dim_x=2, dim_z=1)
                if i == 0:
                    self.f[i].x = np.array([[0.], 
                                            [0.]])  # initial state (acc and velocity)
                elif i == 1:
                    self.f[i].x = np.array([[0.], 
                                            [0.]])
                else:
                    self.f[i].x = np.array([[self.gforce],
                                            [0.]])
                
                self.f[i].F = np.array([[1., self.timestep], 
                                        [0., 1.]])  # state transition matrix
                self.f[i].H = np.array([[1., 0.]])  # Measurement function
                self.f[i].P = np.array([[10., 0.], 
                                        [0., 10.]])  # covariance matrix
                self.f[i].R = np.array([[self.var_acc]])  # measurement noise
        self.f[0].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_x)  # process noise
        self.f[1].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_y)
        self.f[2].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_z)
    
    def filter_acc(self, acc_x:float, acc_y:float, acc_z:float, signal_loss:bool):
        for i in range(3):
            self.f[i].predict()
        if not signal_loss:
            self.f[0].update(acc_x)
            self.f[1].update(acc_y)
            self.f[2].update(acc_z)

    def curve_detector(self, lap_number, lap_diff, timestamp, points):
        if lap_diff == 1:
            if(len(self.one_lap_container_x)>0):
                mean_force_x = mean(self.one_lap_container_x)
                mean_force_y = mean(self.one_lap_container_y)

                self.one_lap_container_x.clear()
                self.one_lap_container_y.clear()
                point = (
                    Point('forcex')
                    .tag('axis', 'x')
                    .field("lap_number", lap_number)
                    .field("mean_force_x", mean_force_x)
                    #.field("mean_force_y", mean_force_y)
                    .time(timestamp)
                )
                points.append(point)

                point = (
                    Point('forcey')
                    .tag('axis', 'y')
                    .field("lap_number", lap_number)
                    .field("mean_force_y", mean_force_y)
                    .time(timestamp)
                )
                points.append(point)

        if float(self.f[1].x[0][0]) > -5. and float(self.f[1].x[0][0]) < 5.:
            self.one_lap_container_y.append(abs(float(self.f[1].x[0][0])))
            self.one_lap_container_x.append(abs(float(self.f[0].x[0][0])))     
                
    def curve_detector_live(self, lap_number, lap_diff, timestamp):
        data_to_send = {}
        if lap_diff == 1:
            if(len(self.one_lap_container_x)>0):
                mean_force_x = mean(self.one_lap_container_x)
                mean_force_y = mean(self.one_lap_container_y)

                self.one_lap_container_x.clear()
                self.one_lap_container_y.clear()

                data_to_send = {
                    "lap_number": lap_number,
                    "mean_force_x": mean_force_x,
                    "mean_force_y": mean_force_y
                }

                return data_to_send

        if float(self.f[1].x[0][0]) > -5. and float(self.f[1].x[0][0]) < 5.:
            self.one_lap_container_y.append(abs(float(self.f[1].x[0][0])))
            self.one_lap_container_x.append(abs(float(self.f[0].x[0][0])))      


    def calc_avg_gforce(self):
        avg_value = abs(np.mean(self.curve_gforces))
        return avg_value

class GYROKalman:
    def __init__(self) -> None:
        self.f = list(range(3))
        self.var_x = 0.5 * 108.17
        self.var_y = 0.5 * 69.2
        self.var_z = 0.5 * 295.38
        self.var_gyro = 0.0000053744 # racebox gyro
        self.timestep = 0.04 # in racebox

# TODO calculate angles in separate function outside the class
    def init_kalman(self):
        for i in range(3):
            self.f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                self.f[i].x = np.array([[0.], 
                                        [0.]])  # initial state (position and velocity)
            elif i == 1:
                self.f[i].x = np.array([[0.], 
                                        [0.]])
            else:
                self.f[i].x = np.array([[0.],
                                        [0.]])
            
            self.f[i].F = np.array([[1., 1/self.timestep], 
                                    [0., 1.]])  # state transition matrix
            self.f[i].H = np.array([[1., 0.]])  # Measurement function
            self.f[i].P = np.array([[0.0004, 0.], 
                                    [0., 0.04]])  # covariance matrix
            self.f[i].R = np.array([[self.var_gyro]])  # measurement noise
        self.f[0].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_x)  # process noise
        self.f[1].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_y)
        self.f[2].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_z)   

    def calc_and_wrap_yaw(self, lon_prev, lat_prev):
        lat1 = math.radians(self.f[0].x[0][0])
        lat2 = math.radians(lat_prev)
        lon1 = math.radians(self.f[1].x[0][0])
        lon2 = math.radians(lon_prev)
        psi_r = math.atan2(math.sin(lon2 - lon1) * math.cos(lat2), math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))
        psi = math.degrees(psi_r)

       # yaw = wrap_angle(psi)

        return psi

    
    def filter_gyro(self, gyro_x:float, gyro_y:float, gyro_z:float, signal_loss:bool):
        for i in range(3):
            self.f[i].predict()
        if not signal_loss:
            self.f[0].update(gyro_x)
            self.f[1].update(gyro_y)
            self.f[2].update(gyro_z)




class TEMPKalman:
    def __init__(self) -> None:

        self.f = list(range(6))
        self.var = 0.5 * 0.0003
        self.var_cooling = 1.
        self.timestep = 1.004987702853438

    def init_kalman(self, engine_in, engine_out, left_in, left_out, right_in, right_out):
        for i in range(6):
            self.f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                self.f[i].x = np.array([[engine_in], 
                                        [0.]])
            elif i == 1:
                self.f[i].x = np.array([[engine_out], 
                                        [0.]])
            elif i == 2:
                self.f[i].x = np.array([[left_in],
                                        [0.]])
            elif i == 3:
                self.f[i].x = np.array([[left_out], 
                                        [0.]])
            elif i == 4:
                self.f[i].x = np.array([[right_in], 
                                        [0.]])
            elif i == 5:
                self.f[i].x = np.array([[right_out], 
                                        [0.]])
            
            self.f[i].F = np.array([[1., self.timestep], 
                                [0., 1.]])  # state transition matrix
            self.f[i].H = np.array([[1., 0.]])  # Measurement function
            self.f[i].P = np.array([[10., 0.], 
                                [0., 10.]])  # covariance matrix
            self.f[i].R = np.array([[self.var_cooling]])  # measurement noise
            self.f[i].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var)  # process noise

    def filter_temperature(self, engine_in, engine_out, lr_in, lr_out, rr_in, rr_out):
        if type(self.f[0]) == int:
            self.init_kalman(engine_in, engine_out, lr_in, lr_out, rr_in, rr_out)
        for i in range(6):
            self.f[i].predict()
        self.f[0].update(engine_in)
        self.f[1].update(engine_out)
        self.f[2].update(lr_in)
        self.f[3].update(lr_out)
        self.f[4].update(rr_in)
        self.f[5].update(rr_out)

def wrap_angle(angle):
    while angle > 360:
        angle -= 360
    while angle < 0:
        angle+=360
    return angle

def mean(array):
    suma = 0
    for value in array:
        suma += value
    result = suma / len(array)
    return result