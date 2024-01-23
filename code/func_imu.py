import csv
from datetime import datetime
from conf_influxdb import *

def import_csv_imu(filepath, date):
  # CSV column names as following:
  # timestamp,gyro_x,gyro_y,gyro_z,acc_x,acc_y,acc_z
  # date like '2023-11-04'
  file = open(filepath, "r")
  csv_reader = csv.DictReader(file)
  line_count = 0
  points = []
  startTime = datetime.now()

  for row in csv_reader:
    #print(f'{row["timestamp"]}; {row["gyro_x"]}; {row["gyro_y"]}; {row["gyro_z"]}; {row["acc_x"]}; {row["acc_y"]}; {row["acc_z"]};')
    org_timestamp = row["timestamp"]
    timestamp = str(date + 'T' + org_timestamp[:8] + '.' + org_timestamp[9:12] + '000Z')

    # gyro_x
    point = (
      Point('gyro')
      .tag("axis", "x")
      .field("gyro_x", int(row["gyro_x"]))
      .time(timestamp)
    )
    points.append(point)
    
    # gyro_y
    point = (
      Point('gyro')
      .tag("axis", "y")
      .field("gyro_y", int(row["gyro_y"]))
      .time(timestamp)
    )
    points.append(point)
    
    # gyro_z
    point = (
      Point('gyro')
      .tag("axis", "z")
      .field("gyro_z", int(row["gyro_z"]))
      .time(timestamp)
    )
    points.append(point)
    
    # acc_x
    point = (
      Point('acc')
      .tag("axis", "x")
      .field("acc_x", int(row["acc_x"]))
      .time(timestamp)
    )
    points.append(point)
    
    # acc_y
    point = (
      Point('acc')
      .tag("axis", "y")
      .field("acc_y", int(row["acc_y"]))
      .time(timestamp)
    )
    points.append(point)
    
    # acc_z
    point = (
      Point('acc')
      .tag("axis", "z")
      .field("acc_z", int(row["acc_z"]))
      .time(timestamp)
    )
    points.append(point)
    
    if line_count % 1000 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  write_api.write(bucket=bucket, org=org, record=points)
  endTime = datetime.now()
  print(f'Imported {line_count} rows in {endTime - startTime}')