import math
import numpy as np
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

class GPSKalman:
    def __init__(self) -> None:
        self.f = list(range(2))
        self.var = 0.5 * 13.08
        self.var_gps = 0.000000000003664 # racebox gps
        self.timestep = 0.04 # in racebox

    def init_kalman(self):
        for i in range(2):
            self.f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                self.f[i].x = np.array([[54.1784337], 
                                        [0.]])  # initial state (position and velocity)
            elif i == 1:
                self.f[i].x = np.array([[18.7130442], 
                                        [0.]])
            
            self.f[i].F = np.array([[1., self.timestep], 
                                    [0., 1.]])  # state transition matrix
            self.f[i].H = np.array([[1., 0.]])  # Measurement function
            self.f[i].P = np.array([[10., 0.], 
                                    [0., 10.]])  # covariance matrix
            self.f[i].R = np.array([[self.var_gps]])  # measurement noise
            self.f[i].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var)  # process noise
        
        #return self.f
    
    def filter_gps(self, lat:float, lon:float, signal_loss:bool):
        for i in range(2):
            self.f[i].predict()
        if not signal_loss:
            self.f[0].update(lat)
            self.f[1].update(lon)

        #return self.f
    
class ACCKalman:
    def __init__(self) -> None:
        self.f = list(range(3))
        self.var_x = 0.5 * 7.58
        self.var_y = 0.5 * 16.4
        self.var_z = 0.5 * 11.5
        self.var_acc = 0.0000053744 # racebox acc
        self.timestep = 0.04 # in racebox
        self.gforce = 9.80665

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
                                        [self.gforce]])
            
            self.f[i].F = np.array([[1., 1/self.timestep], 
                                    [0., 1.]])  # state transition matrix
            self.f[i].H = np.array([[1., 0.]])  # Measurement function
            self.f[i].P = np.array([[10., 0.], 
                                    [0., 10.]])  # covariance matrix
            self.f[i].R = np.array([[self.var_acc]])  # measurement noise
        self.f[0].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_x)  # process noise
        self.f[1].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_y)
        self.f[2].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var_z)

        #return self.f
    
    def filter_acc(self, acc_x:float, acc_y:float, acc_z:float, signal_loss:bool):
        for i in range(3):
            self.f[i].predict()
        if not signal_loss:
            self.f[0].update(acc_x)
            self.f[1].update(acc_y)
            self.f[2].update(acc_z)

        #return self.f

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

        yaw = wrap_angle(psi)

        return yaw

    
    def filter_gyro(self, gyro_x:float, gyro_y:float, gyro_z:float, signal_loss:bool):
        for i in range(3):
            self.f[i].predict()
        if not signal_loss:
            self.f[0].update(gyro_x)
            self.f[1].update(gyro_y)
            self.f[2].update(gyro_z)

        #return self.f



class TEMPKalman:
    def __init__(self) -> None:
        self.f = list(range(6))
        self.var = 0.5 * 0.0003
        self.var_cooling = 1.
        self.timestep = 1.004987702853438

    def init_kalman(self):
        for i in range(6):
            self.f[i] = KalmanFilter(dim_x=2, dim_z=1)
            if i == 0:
                self.f[i].x = np.array([[0.], 
                                        [0.]])  # initial state (position and velocity)
            elif i == 1:
                self.f[i].x = np.array([[0.], 
                                        [0.]])
            elif i == 2:
                self.f[i].x = np.array([[0.],
                                        [0.]])
            elif i == 3:
                self.f[i].x = np.array([[0.], 
                                        [0.]])
            elif i == 4:
                self.f[i].x = np.array([[0.], 
                                        [0.]])
            elif i == 5:
                self.f[i].x = np.array([[0.], 
                                        [0.]])
            
            self.f[i].F = np.array([[1., self.timestep], 
                                [0., 1.]])  # state transition matrix
            self.f[i].H = np.array([[1., 0.]])  # Measurement function
            self.f[i].P = np.array([[10., 0.], 
                                [0., 10.]])  # covariance matrix
            self.f[i].R = np.array([[self.var_cooling]])  # measurement noise
            self.f[i].Q = Q_discrete_white_noise(dim=2, dt=self.timestep, var=self.var)  # process noise

    def filter_temperature(self, engine_in, engine_out, lr_in, lr_out, rr_in, rr_out):
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