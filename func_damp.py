import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *

def import_csv_damp(filepath, start_time):
  # CSV column names as following:
  # timestamp,ID,delta
  # date like '2023-11-04'
  file = open(filepath, "r")
  csv_reader = csv.DictReader(file)
  line_count = 0
  points = []
  startTime = datetime.datetime.now()

  for row in csv_reader:
    #print(f'{row["timestamp"]}; {row["ID"]}; {row["delta"]}')
    timestamp = start_time_add_timestamp(start_time, row["timestamp"])
    point = (
      Point('damp')
      .tag("ID", f'{row["ID"]}')
      .field("delta", int(row["delta"]))
      .time(timestamp)
    )
    points.append(point)
    if line_count % 5000 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  endTime = datetime.datetime.now()
  print(f'DAMP: Imported {line_count} rows in {endTime - startTime}')