import numpy as np
import csv
from conf_influxdb import *
import math
from datetime import datetime
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

def calc_var_acc(file_path):
  with (open(file_path, "r") as file):
        csvreader_object = csv.reader(file)
        for i in range (1, 13):
            next(csvreader_object)
            
        data = csv.DictReader(file)
        acc_data = []
        for i in range(3):
            acc_data.append([])
        for row in data:
            acc_data[0].append(float(row['GForceX']))
            acc_data[1].append(float(row['GForceY']))
            acc_data[2].append(float(row['GForceZ']))
            if len(acc_data[0]) > 1000 and \
                len(acc_data[1]) > 1000 and\
                len(acc_data[2]) > 1000:
                break
        var_x = np.var(acc_data[0])
        var_y = np.var(acc_data[1])
        var_z = np.var(acc_data[2])

        absolute_var = (var_x + var_y + var_z)/3
  return absolute_var


def kalman_acc(f, acc_x, acc_y, acc_z, velocity_x, velocity_y, velocity_z, row_number, var_acc, var_gps):
  timestep = 0.04
  var = 0.0001
  GForce = 9.80665
  if row_number == 0:
    for i in range(3):
      a_m = 19.6
      var_a = 0.5 * a_m
      f[i] = KalmanFilter(dim_x=2, dim_z=2)
      if i == 0:
        f[i].x = np.array([[acc_x], 
                            [0.]])  # initial state (position and velocity)
      elif i == 1:
        f[i].x = np.array([[acc_y], 
                            [0.]])
      else:
        f[i].x = np.array([[acc_z],
                          [GForce]])
      
      f[i].F = np.array([[1., 1/timestep], 
                          [0., 1.]])  # state transition matrix
      f[i].H = np.array([[1., 0.],
                         [0., 1.]])  # Measurement function
      f[i].P = np.array([[10., 0.], 
                          [0., 10.]])  # covariance matrix
      f[i].R = np.array([[var_acc, 0.],
                         [0., var_gps]])  # measurement noise
      f[i].Q = Q_discrete_white_noise(dim=2, dt=timestep, var=var)  # process noise


  f[0].predict()
  f[0].update([acc_x, velocity_x])
  f[1].predict()
  f[1].update([acc_y, velocity_y])
  f[2].predict()
  f[2].update([acc_z, velocity_z])

  return f

def calc_var_gyro(file_path):
  with (open(file_path, "r") as file):
        csvreader_object = csv.reader(file)
        for i in range (1, 13):
            next(csvreader_object)
            
        data = csv.DictReader(file)
        gyro_data = []
        for i in range(3):
            gyro_data.append([])
        for row in data:
            gyro_data[0].append(float(row['GyroX']))
            gyro_data[1].append(float(row['GyroY']))
            gyro_data[2].append(float(row['GyroZ']))
            if len(gyro_data[0]) > 1000 and \
                len(gyro_data[1]) > 1000 and\
                len(gyro_data[2]) > 1000:
                break
        var_x = np.var(gyro_data[0])
        var_y = np.var(gyro_data[1])
        var_z = np.var(gyro_data[2])

        absolute_var = (var_x + var_y + var_z)/3
  return absolute_var



def kalman_gyro(f_gps, f_gyro, f_acc, gyro_x, gyro_y, gyro_z, row_number, x_prev, y_prev, var_gyro):
  timestep = 0.04
  var = 0.001
  
  fi = math.degrees(math.atan2(f_acc[0].x[0][0], math.sqrt(f_acc[1].x[0][0]**2 + f_acc[2].x[0][0]**2)))
  #print(fi)
  theta = math.degrees(math.atan2(f_acc[1].x[0][0], math.sqrt(f_acc[0].x[0][0]**2 + f_acc[2].x[0][0]**2)))
  #fi = math.degrees(math.atan(f_acc[2].x[0][0]/f_acc[1].x[0][0]))
  #theta = math.degrees(math.atan(f_acc[2].x[0][0]/f_acc[0].x[0][0]))
  if row_number == 0:
    psi = 0.
  else:
    lat1 = math.radians(f_gps[0].x[0][0])
    lat2 = math.radians(y_prev)
    lon1 = math.radians(f_gps[1].x[0][0])
    lon2 = math.radians(x_prev)
    
    psi_r = math.atan2(math.sin(lon2 - lon1) * math.cos(lat2), math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))
    psi = math.degrees(psi_r)
    #if psi * f_gyro[2].x[0][0] < 0:
    #   if f_gyro[2].x[0][0] <0:
    #      while psi > 360:
    #        psi -= 360
    #   else:
    #      while psi < 360:
    #        psi+=360
          
    #print(psi)


  if row_number == 0:
    a_m = 201.3
    var_a = 0.5 * a_m
    for i in range(3):
      f_gyro[i] = KalmanFilter(dim_x=2, dim_z=2)
      if i == 0:
        f_gyro[i].x = np.array([[fi], 
                                [0.]])  # initial state (position and velocity)
      elif i == 1:
        f_gyro[i].x = np.array([[theta], 
                                [0.]])
      else:
        f_gyro[i].x = np.array([[psi],
                                [0.]])
      
      f_gyro[i].F = np.array([[1., timestep], 
                              [0., 1.]])  # state transition matrix
      f_gyro[i].H = np.array([[1., 0.],
                              [0., 1.]])  # Measurement function
      f_gyro[i].P = np.array([[10., 0.], 
                              [0., 10.]])  # covariance matrix
      f_gyro[i].R = np.array([[var, 0.],
                              [0., var_gyro]])  # measurement noise
      f_gyro[i].Q = Q_discrete_white_noise(dim=2, dt=timestep, var=var)  # process noise


  f_gyro[0].predict()
  f_gyro[0].update([fi, gyro_x])
  f_gyro[1].predict()
  f_gyro[1].update([theta, gyro_y])
  f_gyro[2].predict()
  f_gyro[2].update([psi, gyro_z])

  return f_gyro, fi, theta, psi

def calc_var_gps(file_path):
  with (open(file_path, "r") as file):
        csvreader_object = csv.reader(file)
        for i in range (1, 13):
            next(csvreader_object)
            
        data = csv.DictReader(file)
        gps_data = []
        for i in range(3):
            gps_data.append([])
        for row in data:
            gps_data[0].append(float(row['Longitude']))
            gps_data[1].append(float(row['Latitude']))
            gps_data[2].append(float(row['Altitude']))
            if len(gps_data[0]) > 1000 and \
                len(gps_data[1]) > 1000 and\
                len(gps_data[2]) > 1000:
                break
        var_x = np.var(gps_data[0])
        var_y = np.var(gps_data[1])
        var_z = np.var(gps_data[2])

        absolute_var = (var_x + var_y + var_z)/3
  return absolute_var

def kalman_gps(f, lat, lon, alt, row_number, var_gps):
  timestep = 0.04
  signal_loss = False
  var = 0.0000001
  if row_number == 0:
    for i in range(3):
      f[i] = KalmanFilter(dim_x=2, dim_z=1)
      if i == 0:
        f[i].x = np.array([[float(lat)], 
                            [0.]])  # initial state (position and velocity)
      elif i == 1:
        f[i].x = np.array([[float(lon)], 
                            [0.]])
      else:
        f[i].x = np.array([[float(alt)],
                            [0.]])
      
      f[i].F = np.array([[1., timestep], 
                          [0., 1.]])  # state transition matrix
      f[i].H = np.array([[1., 0.]])  # Measurement function
      f[i].P = np.array([[10., 0.], 
                          [0., 10.]])  # covariance matrix
      f[i].R = np.array([[var]])  # measurement noise
      f[i].Q = Q_discrete_white_noise(dim=2, dt=timestep, var=var)  # process noise


  if lat != '' and lon != '':
    lat = float(lat)
    lon = float(lon)
    alt = float(alt)
  elif lat == '':
    lat = 0.0
    signal_loss = True
  elif lon != '':
    lon = 0.0
    signal_loss = True
  
  if signal_loss == True:
    f[0].predict()
    f[1].predict()
    f[2].predict()
  else:
    f[0].predict()
    f[0].update(lat)
    f[1].predict()
    f[1].update(lon)
    f[2].predict()
    f[2].update(alt)

  return f

    



