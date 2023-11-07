import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *

def short_timestamp_to_standard_string(org_timestamp):
  int_timestamp = int(org_timestamp)
  minutes = int(int_timestamp / 60000) % 60
  str_minutes = str(minutes)
  if minutes < 10:
    str_minutes = '0' + str_minutes
  seconds = int(int_timestamp / 1000) % 60
  str_seconds = str(seconds)
  if seconds < 10:
    str_seconds = '0' + str_seconds
  timestamp = str('T00:' + str_minutes + ':' + str_seconds + '.' + str(int_timestamp % 1000))
  return timestamp

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
    #timestamp '2023-11-04T11:00:00.000000Z'
    #org_timestamp = row["timestamp"]
    # TODO switch timestamp format
    #timestamp = str(date + 'T' + org_timestamp[:8] + '.' + org_timestamp[9:12] + '000Z')
    #timestamp = str(date + short_timestamp_to_standard_string(org_timestamp))
    timestamp = start_time_add_millis_timestamp(start_time, row["timestamp"])
    print(timestamp)
    point = (
      Point('abs')
      .tag("ID", f'{row["ID"]}')
      .field("speed", float(row["speed"]))
      .time(timestamp)
    )
    points.append(point)
    if line_count % 1000 == 0:
      #write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  endTime = datetime.datetime.now()
  print(f'Imported {line_count} rows in {endTime - startTime}')