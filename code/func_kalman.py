import numpy as np
import csv
from conf_influxdb import *
import math
from datetime import datetime
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

def kalman_acc(f, acc_x, acc_y, acc_z, velocity_x, velocity_y, velocity_z, row_number):
  timestep = 0.04
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
                          [velocity_z]])
      
      f[i].F = np.array([[1., 1/timestep], 
                          [0., 1.]])  # state transition matrix
      f[i].H = np.array([[1., 0.]])  # Measurement function
      f[i].P = np.array([[10., 0.], 
                          [0., 10.]])  # covariance matrix
      f[i].R = np.array([[var]])  # measurement noise
      f[i].Q = Q_discrete_white_noise(dim=2, dt=timestep, var=var)  # process noise


  f[0].predict()
  f[0].update(acc_x)
  f[1].predict()
  f[1].update(acc_y)
  f[2].predict()
  f[2].update(acc_z)

  return f

def kalman_gps(f, lat, lon, alt, row_number):
  timestep = 0.04
  GForce = 9.80665
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
                            [GForce]])
      
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

    



