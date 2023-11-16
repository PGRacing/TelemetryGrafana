import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *

# DEG_TO_MM_FRONT = 1.221374046
# DEG_TO_MM_REAR = 1.070090958
# R_TO_DEG = 100.0
# 100R = 10mm
R_TO_MM = 0.1
REF_VAL_FL = 1080.0
REF_VAL_FR = 1740.0
REF_VAL_RL = 970.0
REF_VAL_RR = 1840.0

# 900R = 90deg
R_TO_DEG_SW = 0.1
REF_VAL_SW = 2380.0

# IDs
# 6  SW steering wheel
# 7  FL Front Left
# 8  FR Front Right
# 11 RL Rear Left
# 12 RR Rear Right

# 7  FL ugiecie zawieszenia - wzrost R
# 8  FR ugiecie zawieszenia - spadek R
# 11 RL ugiecie zawieszenia - wzrost R
# 12 RR ugiecie zawieszenia - spadek R

# 6  SW skret w lewo - wzrost R
# 6  SW skret w prawo - spadek R

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
    raw_value = float(int(row["delta"]))
    delta = 0.0
    match int(row["ID"]):
      case 7:
        delta = - (REF_VAL_FL - raw_value) * R_TO_MM
      case 8:
        delta = (REF_VAL_FR - raw_value) * R_TO_MM
      case 11:
        delta = - (REF_VAL_RL - raw_value) * R_TO_MM
      case 12:
        delta = (REF_VAL_RR - raw_value) * R_TO_MM
      case 6:
        delta = (REF_VAL_SW - raw_value) * R_TO_DEG_SW
    point = (
      Point('damp')
      .tag("ID", f'{row["ID"]}')
      .field("delta", delta)
      .time(timestamp)
    )
    points.append(point)
    if line_count % 5000 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  endTime = datetime.datetime.now()
  print(f'DAMP: Imported {line_count} rows in {endTime - startTime}')