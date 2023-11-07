import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *

def import_csv_gps(filepath):
  # CSV column names as following:
  # timestamp,LOG,utc,pos status,lat,lat dir,lon,lon dir,speed,,track,date,,mag var,var dir,mode ind,chs,ter
  # date like '2023-11-04'
  file = open(filepath, "r")
  csv_reader = csv.DictReader(file)
  line_count = 0
  start_time = 0
  points = []
  startTime = datetime.datetime.now()

  for row in csv_reader:
    if row["timestamp"] and row["date"]:
      start_time = gps_timestamp_sub_timestamp(row["date"], row["utc"], row["timestamp"])
      break

  if start_time == 0:
    return 0
  print(start_time)

  for row in csv_reader:
    #print(f'{row["timestamp"]}; {row["LOG"]}; {row["utc"]}; {row["pos status"]}; {row["lat"]}; {row["lat dir"]}; {row["lon"]}; {row["lon dir"]}; {row["speed"]}; {row["track"]}; {row["date"]}; {row["mode ind"]}')
    org_timestamp = row["timestamp"]
    timestamp = start_time_add_timestamp(start_time, org_timestamp)
    point = (
      Point('gps')
      .tag("pos_status", f'{row["pos status"]}')
      .field("pos_status", row["pos status"])
      .time(timestamp)
    )
    points.append(point)
    if line_count % 1000 == 0:
      #write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  endTime = datetime.datetime.now()
  print(f'GPS: Imported {line_count} rows in {endTime - startTime}')

  return start_time