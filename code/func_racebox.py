import numpy as np
import csv
from conf_influxdb import *
import math
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise


path = 'C:/Users/malwi/Documents/MEGA/PG/PGRacingTeam/telemetry_data/23_11_05_Pszczolki/'

GForce =  9.80665 # m/s2
timestep = 0.04 # s
file_counter = 0
total_rows_calculated = 0
deg_to_met = 111196.672 


def find_racebox(filepath):
  global file_counter
  for i in range (1, 16):
    file_counter += 1
    kalman(filepath + 'RB-' + str(i) + '.csv')
    print(f'Import of file number {file_counter} finished')
  print(f'Successfully calculated {total_rows_calculated} lines!')
    

def kalman(filefullpath):
  global total_rows_calculated
  file = open(filefullpath, 'r')
  csvreader_object = csv.reader(file)
  for i in range (1, 13):
      next(csvreader_object)
      
  data = csv.DictReader(file)
  row_counter = 0
  points = []

  f = list(range(2))
  for row in data:
    signal_loss = False
    row_counter += 1
    total_rows_calculated += 1
    #print(f'File: {file_counter}, Row: {row_counter}')

    row['GForceX'] = float(row['GForceX']) * GForce 
    row['GForceY'] = float(row['GForceY']) * GForce 
    row['GForceZ'] = float(row['GForceZ']) * GForce

    row['GyroX'] = float(row['GyroX'])
    row['GyroY'] = float(row['GyroY'])
    row['GyroZ'] = float(row['GyroZ'])

    if row['Latitude'] != '' and row['Longitude'] != '' and row['Speed'] != '':
      row['Latitude'] = float(row['Latitude'])
      row['Longitude'] = float(row['Longitude'])
      speed_mps = float(row['Speed']) * (10/36)
    elif row['Latitude'] == '':
      row['Latitude'] = 0.0
      signal_loss = True
    elif row['Longitude'] != '':
       row['Longitude'] = 0.0
       signal_loss = True
    elif row['Speed'] != '':
       row['Speed'] = 0.0
       signal_loss = True
  

    if row_counter == 1:
      var = 0.0000001
      for i in range(2):
        f[i] = KalmanFilter(dim_x=2, dim_z=1)
        if i == 0:
          f[i].x = np.array([[row['Latitude']], 
                              [row['GyroZ']]])  # initial state (position and velocity)
        else:
          f[i].x = np.array([[row['Longitude']], 
                              [row['GyroZ']]])
        
        f[i].F = np.array([[1., timestep], 
                            [0., 1.]])  # state transition matrix
        f[i].H = np.array([[1., 0.]])  # Measurement function
        f[i].P = np.array([[10., 0.], 
                            [0., 10.]])  # covariance matrix
        # proces noise and measurement noise needs to be fine tuned
        # measurement noise smaller -> kalman filter follows raw data more closely
        # process noise bigger -> kalman filter follows raw data more closely
        # but this need to be checked
        f[i].R = np.array([[var]])  # measurement noise
        f[i].Q = Q_discrete_white_noise(dim=2, dt=timestep, var=var)  # process noise
    
    if signal_loss == True:
      f[0].predict()
      f[0].update(lat_previous + lat_delta)
      f[1].predict()
      f[1].update(lon_previous + lon_delta)
    else:
      f[0].predict()
      f[0].update(row['Latitude'])
      f[1].predict()
      f[1].update(row['Longitude'])

    if row_counter >= 2:
      lat_delta = float(f[0].x[0][0]) - lat_previous
      lon_delta = float(f[1].x[0][0]) - lon_previous

    lat_previous = float(f[0].x[0][0])
    lon_previous = float(f[1].x[0][0])
    
    # latitude and longitude
    point = (
      Point('gps')
      .tag('ID', 'gps_position')
      .field('latitude', float(f[0].x[0][0]))
      .field('longitude', float(f[1].x[0][0]))
      .time(row['Time'])
    )
    points.append(point)

    # speed
    point = (
        Point('spd')
        .tag('Record', "velocity")
        .field('speed', float(row['Speed']))
        .time(row['Time'])
        )
    points.append(point)
    
    # gyro_x
    point = (
      Point('gyro')
      .tag("axis", "x")
      .field("gyro_x", row["GyroX"])
      .time(row['Time'])
    )
    points.append(point)
    
    # gyro_y
    point = (
      Point('gyro')
      .tag("axis", "y")
      .field("gyro_y", row["GyroY"])
      .time(row['Time'])
    )
    points.append(point)
    
    # gyro_z
    point = (
      Point('gyro')
      .tag("axis", "z")
      .field("gyro_z", row["GyroZ"])
      .time(row['Time'])
    )
    points.append(point)
    
    # acc_x
    point = (
      Point('acc')
      .tag("axis", "x")
      .field("acc_x", row["GForceX"])
      .time(row['Time'])
    )
    points.append(point)
    
    # acc_y
    point = (
      Point('acc')
      .tag("axis", "y")
      .field("acc_y", row["GForceY"])
      .time(row['Time'])
    )
    points.append(point)
    
    # acc_z
    point = (
      Point('acc')
      .tag("axis", "z")
      .field("acc_z", row["GForceZ"])
      .time(row['Time'])
    )
    points.append(point)

    if row_counter % 555 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()

  








def linear_kalman(filefullpath):
    file = open(filefullpath, 'r')
    csvreader_object = csv.reader(file)
    for i in range (1, 13):
        next(csvreader_object)
        
    data = csv.DictReader(file)
    row_counter = 0
   
    points = []
    line_count = 0
    
    angular_position = math.radians(90)
    
    C = np.array([[1, 0, 0, 0],
                  [0, 1, 0, 0]])
    
    A = np.array([[1, 0, timestep, 0],
                  [0, 1, 0, timestep],
                  [0, 0, 1, 0],
                  [0, 0, 0, 1]])
    

    latitude_new = 0
    longitude_new = 0
    
    x_old = np.array([[0],
                      [0],
                      [0],
                      [0]])
    longitude_old = 0
    latitude_old = 0
    
    
    for row in data:
        row_counter += 1
        line_count += 1
        
        
        print(f'Row: {row_counter}')
        
        
        row['GForceX'] = float(row['GForceX']) * GForce 
        row['GForceY'] = float(row['GForceY']) * GForce 
        row['GForceZ'] = float(row['GForceZ']) * GForce
        
        row['GyroX'] = float(row['GyroX'])
        row['GyroY'] = float(row['GyroY'])
        row['GyroZ'] = float(row['GyroZ'])
        
        if ((row['Latitude'] != '') and (row['Longitude'] != '')):
            row['Latitude'] = float(row['Latitude']) # y
            row['Longitude'] = float(row['Longitude']) # x
                
        
        if row_counter == 1:

            longitude_old = row['Longitude']
            latitude_old = row['Latitude']
            velocity_x = row['GForceX'] * timestep
            velocity_y = row['GForceY'] * timestep
            
            x_old = np.array([[longitude_old],
                              [latitude_old],
                              [velocity_x],
                              [velocity_y]])
        
        
        
        if row_counter > 1:
            angular_position_delta = (row['GyroZ'] * timestep)/10  + 0.5 * row['GForceZ'] * (timestep**2)
            angular_position += angular_position_delta
            
        #    angular_acceleration = angular_position_delta / timestep
            
        #    print(math.degrees(angular_position))

        #    velocity_x_delta = (row['GyroX'] * math.cos(angular_position) + row['GForceX'] * timestep)
        #    velocity_y_delta = row['GyroY'] * math.cos(angular_position) + row['GForceY'] * timestep
            
            velocity_x_delta = row['GForceX'] * timestep
            velocity_y_delta = row['GForceY'] * timestep 
            
            velocity_x += velocity_x_delta
            velocity_y += velocity_y_delta
            
            x_old = np.array([[longitude_old],
                              [latitude_old],
                              [velocity_x],
                              [velocity_y]])

            x_new = A @ x_old
           
            y = C @ x_new
           
            latitude_new = latitude_old + (velocity_y * timestep)/deg_to_met
            longitude_new = longitude_old + (velocity_x * timestep)/(deg_to_met) #* math.cos(math.radians(latitude_new)))
            
            
            if ((row['Longitude'] == '') or (row['Latitude'] == '')):
                longitude_correction = longitude_new #float(y[0][0])
                latitude_correction = latitude_new  #float(y[1][0])
            else:
                longitude_correction = (longitude_new + row['Longitude']) / 2
                latitude_correction = (latitude_new + row['Latitude']) / 2
                

            longitude_new = longitude_correction
            latitude_new = latitude_correction
           
    #       if latitude_correction == 0:
    #           print(row['Record'])
    #           break
    #       velocity_x_old = velocity_x_new
    #        velocity_y_old = velocity_y_new
            x_old = x_new
            longitude_old = longitude_new
            latitude_old = latitude_new
           
            #latitude, longitude
            point = (
              Point('gps')
              .tag('ID', 'gps_position')
              .field('latitude', latitude_correction)
              .field('longitude', longitude_correction)
              .time(row['Time'])
            )
            points.append(point)
            
            #speed
            point = (
                Point('spd')
                .tag('Record', "velocity")
                .field('speed', float(row['Speed']))
                .time(row['Time'])
                )
            points.append(point)
            
            # gyro_x
            point = (
              Point('gyro')
              .tag("axis", "x")
              .field("gyro_x", float(row["GyroX"]))
              .time(row['Time'])
            )
            points.append(point)
            
            # gyro_y
            point = (
              Point('gyro')
              .tag("axis", "y")
              .field("gyro_y", float(row["GyroY"]))
              .time(row['Time'])
            )
            points.append(point)
            
            # gyro_z
            point = (
              Point('gyro')
              .tag("axis", "z")
              .field("gyro_z", float(row["GyroZ"]))
              .time(row['Time'])
            )
            points.append(point)
            
            # acc_x
            point = (
              Point('acc')
              .tag("axis", "x")
              .field("acc_x", float(row["GForceX"]))
              .time(row['Time'])
            )
            points.append(point)
            
            # acc_y
            point = (
              Point('acc')
              .tag("axis", "y")
              .field("acc_y", float(row["GForceY"]))
              .time(row['Time'])
            )
            points.append(point)
            
            # acc_z
            point = (
              Point('acc')
              .tag("axis", "z")
              .field("acc_z", float(row["GForceZ"]))
              .time(row['Time'])
            )
            points.append(point)
           
   
            if row_counter % 555 == 0:
              write_api.write(bucket=bucket, org=org, record=points)
              points.clear()
            line_count += 1

            
            
       #     angular_position_old = angular_position_new
      #      velocity_x_old = velocity_x_new
      #      velocity_y_old = velocity_y_new
            

find_racebox(path)