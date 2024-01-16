import numpy as np
import csv
from conf_influxdb import *
from func_kalman import *
import math
from datetime import datetime
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise


path = 'C:/Users/malwi/Documents/MEGA/PG/PGRacingTeam/telemetry_data/23_11_05_Pszczolki/'

GForce =  9.80665 # m/s2
timestep = 0.04 # s
file_counter = 0


# to be set every track change
approx_lon = 18.712
approx_lat = 54.178

conv_rate_lon = math.cos(approx_lat) * (40075000/360) # deg to met
conv_rate_lat = 111111.0


def find_racebox(filepath):
  global file_counter
  for i in range (1, 16):
    file_counter += 1
    #print(f'file {file_counter}')
    open_file(filepath + 'RB-' + str(i) + '.csv')
    #kalman_one_value(filepath + 'RB-' + str(i) + '.csv')
    #angular_acceleration(filepath + 'RB-' + str(i) + '.csv')
  print(f'Successfully imported {file_counter} files!')

def open_file(filefullpath):
  file = open(filefullpath, 'r')
  csvreader_object = csv.reader(file)
  for i in range (1, 13):
      next(csvreader_object)
      
  data = csv.DictReader(file)
  points = []
  startTime = datetime.now()
  row_counter = 0

  f_gps = list(range(3))
  f_acc = list(range(3))

  for row in data:
    gyro_x = float(row['GyroX'])
    gyro_y = float(row['GyroY'])
    gyro_z = float(row['GyroZ'])

    GForceX = float(row['GForceX']) * GForce 
    GForceY = float(row['GForceY']) * GForce 
    GForceZ = float(row['GForceZ']) * GForce

    timestamp = row['Time']

    f_gps = kalman_gps(f_gps, row['Latitude'], row['Longitude'], row['Altitude'], row_counter)
    f_acc = kalman_acc(f_acc, GForceX, GForceY, GForceZ, f_gps[0].x[1][0], f_gps[1].x[1][0], f_gps[2].x[1][0], row_counter)

    # latitude and longitude
    point = (
      Point('gps')
      .tag('ID', 'gps_position')
      .field('latitude', float(f_gps[0].x[0][0]))
      .field('longitude', float(f_gps[1].x[0][0]))
      .time(timestamp)
    )
    points.append(point)

    # speed
    point = (
        Point('spd')
        .tag('Record', "velocity")
        .field('speed', float(row['Speed']))
        .time(timestamp)
        )
    points.append(point)
    
    # acc_x
    point = (
      Point('acc')
      .tag("axis", "x")
      .field("acc_x", float(f_acc[0].x[0][0]))
      .time(timestamp)
    )
    points.append(point)
    
    # acc_y
    point = (
      Point('acc')
      .tag("axis", "y")
      .field("acc_y", float(f_acc[1].x[0][0]))
      .time(timestamp)
    )
    points.append(point)
    
    # acc_z
    point = (
      Point('acc')
      .tag("axis", "z")
      .field("acc_z", float(f_acc[2].x[0][0]))
      .time(timestamp)
    )
    points.append(point)
    row_counter += 1

    if row_counter % 555 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()

  

  endTime = datetime.now()
  print(f'Calculated file number {file_counter} in {endTime - startTime}')


def calculate_angles(f_acc, yaw_previous):
   roll_angle = math.atan2(f_acc[1].x[0][0], f_acc[2].x[0][0])
   pitch_angle = math.atan2(-f_acc[0].x[0][0], math.sqrt((f_acc[1].x[0][0])**2) + (f_acc[2].x[0][0])**2)
   yaw_angle = yaw_previous + 



def angular_acceleration(filefullpath):
  file = open(filefullpath, 'r')
  csvreader_object = csv.reader(file)
  for i in range (1, 13):
      next(csvreader_object)
      
  data = csv.DictReader(file)
  row_counter = 0
  points = []
  startTime = datetime.now()

  for row in data:
    row['GyroX'] = float(row['GyroX'])
    row['GyroY'] = float(row['GyroY'])
    row['GyroZ'] = float(row['GyroZ'])

    if row_counter == 0:
      previous_value_x = 0.
      previous_value_y = 0.
      previous_value_z = 0.

    angular_acc_x = (row['GyroX'] - previous_value_x)/timestep
    angular_acc_y = (row['GyroY'] - previous_value_y)/timestep
    angular_acc_z = (row['GyroZ'] - previous_value_z)/timestep

    previous_value_x = row['GyroX']
    previous_value_y = row['GyroY']
    previous_value_z = row['GyroZ']

    # gyro_x
    point = (
      Point('gyro')
      .tag('axis', 'x')
      .field('gyro_x', row["GyroX"])
      .time(row['Time'])
    )
    points.append(point)

    # angular acceleration x
    point = (
      Point('angular_acc')
      .tag('axis', 'x')
      .field('angular_acc_x', angular_acc_x)
      .time(row['Time'])
    )
    points.append(point)
    
    # gyro_y
    point = (
      Point('gyro')
      .tag('axis', 'y')
      .field('gyro_y', row["GyroY"])
      .time(row['Time'])
    )
    points.append(point)

    # angular acceleration y
    point = (
      Point('angular_acc')
      .tag('axis', 'y')
      .field('angular_acc_y', angular_acc_y)
      .time(row['Time'])
    )
    points.append(point)
    
    # gyro_z
    point = (
      Point('gyro')
      .tag('axis', 'z')
      .field('gyro_z', row["GyroZ"])
      .time(row['Time'])
    )
    points.append(point)

    # angular acceleration z
    point = (
      Point('angular_acc')
      .tag('axis', 'z')
      .field('angular_acc_z', angular_acc_z)
      .time(row['Time'])
    )
    points.append(point)

    if row_counter % 555 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()

    row_counter += 1
  endTime = datetime.now()
  print(f'GYRO: calculations finished in {endTime - startTime}')

def import_acc(filefullpath):
  file = open(filefullpath, 'r')
  csvreader_object = csv.reader(file)
  for i in range (1, 13):
      next(csvreader_object)
      
  data = csv.DictReader(file)
  row_counter = 0
  points = []
  startTime = datetime.now()
  for row in data:
    row['GForceX'] = float(row['GForceX']) * GForce 
    row['GForceY'] = float(row['GForceY']) * GForce 
    row['GForceZ'] = float(row['GForceZ']) * GForce
    
    acc_x, acc_y, acc_z = kalman_acc(float(row['GForceX']), row['GForceY'], row['GForceX'], )

def kalman(filefullpath):
  file = open(filefullpath, 'r')
  csvreader_object = csv.reader(file)
  for i in range (1, 13):
      next(csvreader_object)
      
  data = csv.DictReader(file)
  row_counter = 0
  points = []
  startTime = datetime.now()

  f = KalmanFilter(dim_x=4, dim_z=2)
  for row in data:
    signal_loss = False
    row_counter += 1
    total_rows_calculated += 1

    #timestamp = time_correction(row['Time'])
    timestamp = row['Time']

    

    if row['Latitude'] != '' and row['Longitude'] != '':
      row['Latitude'] = float(row['Latitude'])
      row['Longitude'] = float(row['Longitude'])

    elif row['Latitude'] == '':
      row['Latitude'] = 0.0
      signal_loss = True
    elif row['Longitude'] != '':
      row['Longitude'] = 0.0
      signal_loss = True
  

    if row_counter == 1:
      var = 10
      f.x = np.array([[row['Latitude']*conv_rate_lat],
                      [row['Longitude']*conv_rate_lon],
                      [0.],
                      [0.]])  # initial state (position and velocity)
        
      f.F = np.array([[1., 0., timestep, 0.], 
                      [0., 1., 0., timestep],
                      [0., 0., 1., 0.],
                      [0., 0., 0., 1.]])  # state transition matrix
      f.H = np.array([[1., 0., 0., 0.],
                      [0., 1., 0., 0.]])  # Measurement function
      f.P = np.array([[10., 0., 0., 0.], 
                      [0., 10., 0., 0.],
                      [0., 0., 10., 0.],
                      [0., 0., 0., 10.]])  # covariance matrix

      f.R = np.array([[var**2, 0.],
                      [0., var**2]])  # measurement noise

      f.Q = Q_discrete_white_noise(dim=4, dt=timestep, var=var)  # process noise
    
    if signal_loss == True:
      f.predict()
    else:
      f.predict()
      f.update(np.array([[row['Latitude']*conv_rate_lat],
                         [row['Longitude']*conv_rate_lon]]))
    
    # latitude and longitude
    point = (
      Point('gps')
      .tag('ID', 'gps_position')
      .field('latitude', float(f.x[0][0])*(1/conv_rate_lat))
      .field('longitude', float(f.x[1][0])*(1/conv_rate_lon))
      .time(timestamp)
    )
    points.append(point)

    # speed
    point = (
        Point('spd')
        .tag('Record', "velocity")
        .field('speed', float(row['Speed']))
        .time(timestamp)
        )
    points.append(point)

    point = (
        Point('spd')
        .tag('Record', "velocity_x")
        .field('speed_x', float(f.x[2][0]))
        .time(timestamp)
        )
    points.append(point)

    point = (
        Point('spd')
        .tag('Record', "velocity_y")
        .field('speed_y', float(f.x[3][0]))
        .time(timestamp)
        )
    points.append(point)
    
    # acc_x
    point = (
      Point('acc')
      .tag("axis", "x")
      .field("acc_x", row["GForceX"])
      .time(timestamp)
    )
    points.append(point)
    
    # acc_y
    point = (
      Point('acc')
      .tag("axis", "y")
      .field("acc_y", row["GForceY"])
      .time(timestamp)
    )
    points.append(point)
    
    # acc_z
    point = (
      Point('acc')
      .tag("axis", "z")
      .field("acc_z", row["GForceZ"])
      .time(timestamp)
    )
    points.append(point)

    if row_counter % 555 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
  
  endTime = datetime.now()
  print(f'GPS: import finished in {endTime - startTime}')

  





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