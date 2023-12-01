import numpy as np
import csv
import pandas as pd
from conf_influxdb import *
import math


path = 'C:/Users/malwi/Documents/MEGA/PG/PGRacingTeam/telemetry/23_11_05_Pszczolki/'

GForce =  9.80665 # m/s2
timestep = 0.04 # s
conversion_rate = 1000000.0 # km/s2 to m/s2
row_counter = 0

def find_acc(filepath):
    for i in range (1, 16):
  #      print('ACC-' + str(i) + '.csv')
        import_acc(filepath + 'ACC-' + str(i) + '.csv')


def import_acc(filefullpath):
    global GForce
    global timestep
    global conversion_rate
    global row_counter
    
    # [0]Record,[1]Time,[2]Latitude,[3]Longitude,[4]Altitude,[5]Speed,
    # [6]GForceX,[7]GForceY,[8]GForceZ,[9]Lap,[10]GyroX,[11]GyroY,[12]GyroZ
    
    # speed in km/h
    # GyroX, GyroY, GyroZ in rad/s
    # GForceX, GForceY, GForceZ in km/s2
    
    # p = GyroX, q = GyroY, r = GyroZ
    
    # date like 2023-11-05T08:01:59.280Z (date T time Z)
    file = open(filefullpath, 'r')
    csvreader_object = csv.reader(file)
    for i in range (1, 13):
        next(csvreader_object)
        
    data = csv.DictReader(file)
    
    print(data)
    # NOT SURE!!!!!!!!!!!!!!!!!!!!
    variance_phi = 0.01
    variance_theta = 0.01
    
    
    
    variance_gps = 0.01  # (10 cm)^2
    
    Q = np.array([
                [variance_phi, 0, 0, 0],
                [0, variance_theta, 0, 0],
                [0, 0, variance_gps, 0],
                [0, 0, 0, variance_gps]
                ])
    
    
 #   P = np.array([[0, 0], [0, 0]])
    P = np.eye(4)
    R = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]])
    
    points = []
    line_count = 0
    
    
    for row in data:
        row_counter += 1
        
        if row_counter == 1:
            x_hat_previous = np.array([[0], [0], [float(row['Latitude'])], [float(row['Longitude'])]])

        
        p = float(row['GyroX']) #10
        q = float(row['GyroY']) #11
        r = float(row['GyroZ']) #12
        

        row['GForceX'] = float(row['GForceX']) * conversion_rate # 6
        row['GForceY'] = float(row['GForceY']) * conversion_rate # 7
        row['GForceZ'] = float(row['GForceZ']) * conversion_rate # 8
        
        # acceleration is now in m/s2 !!!!!!!!!!!!
            
        
        # roll angle estimate, pitch angle estimate
        # in radians
        phi_hat_rad = math.atan(row['GForceY'] / row['GForceZ'])
        theta_hat_rad = math.asin(row['GForceX'] / GForce)     
        
        # transforming body rates to Euler rates
        phi_dot_rad = float(row["GyroX"]) * math.tan(theta_hat_rad) * (math.sin(phi_hat_rad) * float(row['GyroY']) + math.cos(phi_hat_rad) * float(row['GyroZ']))
        theta_dot_rad = math.cos(phi_hat_rad) * float(row['GyroY']) - math.sin(phi_hat_rad) * float(row['GyroZ'])
        
        # integrate  Euler rates to get estimate of roll and pitch angles
        phi_hat_rad = phi_hat_rad + timestep * phi_dot_rad
        theta_hat_rad = theta_hat_rad + timestep * theta_dot_rad

        # EKF step1: prediction
        
        
        #state estimate
        x_hat = np.array([[phi_hat_rad], [theta_hat_rad], [row['GForceX']], [row['GForceY']]])
        
        if row_counter >= 1:
            x_hat = np.array([[phi_hat_rad * timestep], [theta_hat_rad * timestep]])

        # Euler rates
        f_x_hat_u = [[phi_dot_rad], [theta_dot_rad]]

        f_x_hat_u = [[1 * p + (math.sin(phi_hat_rad) * math.tan(theta_hat_rad)) * q + math.cos(phi_hat_rad) * math.tan(theta_hat_rad) * 3],
                    [0 * p + math.cos(phi_hat_rad) * q + (-1) * math.sin(phi_hat_rad) * r]]

        phi_hat_rad += (timestep * phi_dot_rad)
        theta_hat_rad += (timestep * theta_dot_rad)


 #       A = np.array([[0, (-1) * math.sin(theta_hat_rad) - r * math.cos(theta_hat_rad)],
  #           [(-1) * q * math.sin(phi_hat_rad) - r * math.cos(phi_hat_rad), 0]])
        
        A = np.array([
                    [0, (-1) * math.sin(theta_hat_rad) - r * math.cos(theta_hat_rad), 0, 0],
                    [(-1) * q * math.sin(phi_hat_rad) - r * math.cos(phi_hat_rad), 0, 0, 0],
                    [0, 0, 0, (-1) * math.sin(theta_hat_rad) - r * math.cos(theta_hat_rad)],
                    [0, 0, (-1) * q * math.sin(phi_hat_rad) - r * math.cos(phi_hat_rad), 0]
                    ])
        
        
        # noise
        
        
        
        
   #     Q = np.array([[0, 0], [0, 0]])
        


        # Perform matrix multiplication and transposition
        result = P + timestep * (A @ P @ A.T + Q)
        P = result
        
        # step2: update
        
        sp = math.sin(phi_hat_rad)
        cp = math.cos(phi_hat_rad)
        st = math.sin(theta_hat_rad)
        ct = math.cos(theta_hat_rad)
        
        h = np.array([[GForce * st], [(-1.0) * GForce * ct * sp], [(-1.0) * GForce * ct * cp], [x_hat_previous[2][0]], [x_hat_previous[3][0]]])
#        h = np.array([GForce * st, (-1.0) * GForce * ct * sp, (-1.0) * GForce * ct * cp])
  #      y = np.array([float(row['GForceX']), float(row['GForceY']), float(row['GForceZ'])])
        
        y = np.array([
                    row['GForceX'],
                    row['GForceY'],
                    row['GForceZ'],
                    phi_hat_rad,  
                    theta_hat_rad,  
                    float(row['Latitude']),  
                    float(row['Longitude'])  
                    ])
        
        
        # Jacobian of h(x, u)
#        C = np.array([[0.0, GForce * ct], [(-1.0) * GForce * cp * ct, GForce * sp * st], [GForce * sp * ct, GForce * cp * st]])

        C = np.array([
                    [0.0, GForce * ct, 0, 0],
                    [(-1.0) * GForce * cp * ct, GForce * sp * st, 0, 0],
                    [GForce * sp * ct, GForce * cp * st, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                    ])


        print(C)
        print(P)
        print(C @ P @ C.T + R)

        # Calculate Kalman gain
        K = P @ C.T @ np.linalg.inv(C @ P @ C.T + R)

        if row_counter == 1:
            x_hat = K @ (y - h)
        else:
            x_hat = x_hat_previous + K @ (y - h)
        
        x_hat_previous = x_hat

        P = (np.eye(4) - K @ C) @ P
        
        latitude_correction = x_hat[2]
        longitude_correction = x_hat[3]

        # MEASUREMENT UPDATE
      
#        latitude = float(row['Latitude'])
 #       longitude = float(row['Longitude'])
        
    #    H = np.concatenate((np.eye(2), np.zeros((2, 2))))
 #       measurement = np.array([latitude, longitude])
       # x_hat = x_hat.reshape((2, 1))
       

#       print(C @ x_hat)
       
 #       innovation = measurement - C @ x_hat
 #       x_hat_ = x_hat + K @ np.concatenate((innovation, np.zeros((2, 1))))

#        fused_states.append(x_hat_)
                            
        point = (
          Point('gps_2')
          .tag("_measurement", "gps_position")
          .field("latitude", latitude_correction)
          .time(time)
        )
        points.append(point)
        point = (
          Point('gps_2')
          .tag("_measurement", "gps_position")
          .field("longitude", longitude_correction)
          .time(time)
        )
        points.append(point)

        if row_counter % 1000 == 0:
          write_api.write(bucket=bucket, org=org, record=points)
          points.clear()
        line_count += 1

print(f'Rows calculated: {row_counter}')
find_acc(path)
