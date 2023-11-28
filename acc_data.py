import numpy as np
import csv
import pandas as pd
from conf_influxdb import *
import math


path = 'C:/Users/malwi/Documents/MEGA/PG/PGRacingTeam/telemetry/23_11_05_Pszczolki/'

GForce =  9.80665 # m/s2
timestep = 0.04 # s
conversion_rate = 1000 # km/s2 to m/s2

def find_acc(filepath):
    for i in range (1, 16):
        import_acc(filepath + 'ACC-' + str(i) + '.csv')


def import_acc(filefullpath):
    global GForce
    global timestep
    global conversion_rate
    
    # [0]Record,[1]Time,[2]Latitude,[3]Longitude,[4]Altitude,[5]Speed,
    # [6]GForceX,[7]GForceY,[8]GForceZ,[9]Lap,[10]GyroX,[11]GyroY,[12]GyroZ
    
    # speed in km/h
    # GyroX, GyroY, GyroZ in rad/s
    # GForceX, GForceY, GForceZ in km/s2
    
    # p = GyroX, q = GyroY, r = GyroZ
    
    # date like 2023-11-05T08:01:59.280Z (date T time Z)
    file = open(filefullpath, 'r')
    data = pd.read_csv(file, skiprows=12)
    
    x_hat_previous = 0
    
    P = np.array([[0, 0], [0, 0]])
    R = np.array([[0, 0], [0, 0]])
    
    fused_states = []
    
    
    for row in data:
        
        p = row[10]
        q = row[11]
        r = row[12]
        
        
        
        row[6] *= conversion_rate
        row[7] *= conversion_rate
        row[8] *= conversion_rate
        
        # acceleration is now in m/s2 !!!!!!!!!!!!
            
        
        # roll angle estimate, pitch angle estimate
        # in radians
        phi_hat_rad = math.atan(float(row[7]) / float(row[8]))
        theta_hat_rad = math.asin(float(row[6]) / GForce)     
        
        # transforming body rates to Euler rates
        phi_dot_rad = float(row[10]) * math.tan(theta_hat_rad) * (math.sin(phi_hat_rad) * float(row[11]) + math.cos(phi_hat_rad) * float(row[12]))
        theta_dot_rad = math.cos(phi_hat_rad) * float(row[11]) - math.sin(phi_hat_rad) * float(row[12])
        
        # integrate  Euler rates to get estimate of roll and pitch angles
        phi_hat_rad = phi_hat_rad + timestep * phi_dot_rad
        theta_hat_rad = theta_hat_rad + timestep * theta_dot_rad

        # EKF step1: prediction
        
        
        #state estimate
        x_hat = [[phi_hat_rad], [theta_hat_rad]]
        
        if row >= 1:
            x_hat = [[phi_hat_rad * timestep], [theta_hat_rad * timestep]]

        # Euler rates
        f_x_hat_u = [[phi_dot_rad], [theta_dot_rad]]

        f_x_hat_u = [[1 * p + (math.sin(phi_hat_rad) * math.tan(theta_hat_rad)) * q + math.cos(phi_hat_rad) * math.tan(theta_hat_rad) * 3]
                    [0 * p + math.cos(phi_hat_rad) * q + (-1) * math.sin(phi_hat_rad) * r]]

        phi_hat_rad += (timestep * phi_dot_rad)
        theta_hat_rad += (timestep * theta_dot_rad)


        A = np.array([[0, (-1) * math.sin(theta_hat_rad) - r * math.cos(theta_hat_rad)]
             [(-1) * q * math.sin(phi_hat_rad) - r * math.cos(phi_hat_rad), 0]])

        # noise
        Q = np.array([[0, 0], [0, 0]])
        


        # Perform matrix multiplication and transposition
        result = P + timestep * (np.dot(A, P) + np.dot(P, A.T) + Q)
        P = result
        
        # step2: update
        
        sp = math.sin(phi_hat_rad)
        cp = math.cos(phi_hat_rad)
        st = math.sin(theta_hat_rad)
        ct = math.cos(theta_hat_rad)
        
        h = np.array([GForce * st, (-1.0) * GForce * ct * sp, (-1.0) * GForce * ct * cp])
        y = np.array([row[6], row[7], row[8]])
        
        # Jacobian of h(x, u)
        C = np.array([0.0, GForce * ct, (-1.0) * GForce * cp * ct, GForce * sp * st, GForce * sp * ct, GForce * cp * st])

        # Calculate Kalman gain
        K = P @ C.T @ np.linalg.inv(C @ P @ C.T + R)

        x_hat = x_hat_previous + K @ (y - h)
        
        x_hat_previous = x_hat

        P = (np.eye(len(x_hat)) - K @ C) @ P

        # MEASUREMENT UPDATE
        
        



