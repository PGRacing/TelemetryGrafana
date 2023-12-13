import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *

def import_csv_abs(filepath, start_time):
  # CSV column names as following:
  # timestamp,ID,speed
  # date like '2023-11-04'
  file = open(filepath, "r")
  csv_reader = csv.DictReader(file)
  line_count = 0
  points = []
  startTime = datetime.datetime.now()

  for row in csv_reader:
    #print(f'{row["timestamp"]}; {row["ID"]}; {row["speed"]}')
    # TODO switch timestamp format
    timestamp = start_time_add_millis_timestamp(start_time, row["timestamp"])
    point = (
      Point('abs')
      .tag("ID", f'{row["ID"]}')
      .field("speed", float(row["speed"]) * 2.0)
      .time(timestamp)
    )
    points.append(point)
    if line_count % 5000 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  endTime = datetime.datetime.now()
  print(f'ABS: Imported {line_count} rows in {endTime - startTime}')