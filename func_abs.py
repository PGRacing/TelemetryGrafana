import csv
from datetime import datetime
from conf_influxdb import *

def import_csv_abs(filepath, date):
  # CSV column names as following:
  # timestamp,ID,speed
  # date like '2023-11-04'
  file = open(filepath, "r")
  csv_reader = csv.DictReader(file)
  line_count = 0
  points = []
  startTime = datetime.now()

  for row in csv_reader:
    #print(f'{row["timestamp"]}; {row["ID"]}; {row["speed"]}')
    org_timestamp = row["timestamp"]
    timestamp = str(date + 'T' + org_timestamp[:8] + '.' + org_timestamp[9:12] + '000Z')
    # TODO discuss timestamp format
    point = (
      Point('abs')
      .tag("ID", f'{row["ID"]}')
      .field("speed", int(row["speed"]))
      .time(timestamp)
    )
    points.append(point)
    if line_count % 1000 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  endTime = datetime.now()
  print(f'Imported {line_count} rows in {endTime - startTime}')