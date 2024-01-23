import csv
from datetime import datetime
from code.conf_influxdb import *
from code.utils_timestamp import *
from code.test_functions.filters import low_pass_filter, get_alpha

low_pass_filter_alpha_4Hz = get_alpha(0.004, 4)

def import_csv_abs(filepath, start_time):
  # CSV column names as following:
  # timestamp,ID,speed
  # date like '2023-11-04'
  file = open(filepath, "r")
  csv_reader = csv.DictReader(file)
  line_count = 0
  points = []
  startTime = datetime.datetime.now()
  previous_timestamp = None
  previous_csv_timestamp = None
  prev_speed = [0.0,0.0]

  for row in csv_reader:
    #print(f'{row["timestamp"]}; {row["ID"]}; {row["speed"]}')
    # TODO switch timestamp format
    if line_count < 2:
      first_timestamp_millis = correct_init_time_millis(int(row["timestamp"]))
      timestamp = start_time + first_timestamp_millis
    else:
      csv_timestamp = csv_millis_timestamp_to_timedelta(row["timestamp"])
      timestamp = correct_csv_timestamp_millis(previous_csv_timestamp, csv_timestamp, previous_timestamp)
    if line_count % 2 == 1:
      previous_timestamp = timestamp
      previous_csv_timestamp = row["timestamp"]

    speed = low_pass_filter(float(row["speed"])*2.0, prev_speed[int(row["ID"])-4], low_pass_filter_alpha_4Hz)
    prev_speed[int(row["ID"])-4] = speed
    point = (
      Point('abs')
      .tag("ID", f'{row["ID"]}')
      .field("speed", speed)
      .time(timestamp)
    )
    points.append(point)
    if line_count % 5000 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  write_api.write(bucket=bucket, org=org, record=points)
  endTime = datetime.datetime.now()
  print(f'ABS: Imported {line_count} rows in {endTime - startTime}')