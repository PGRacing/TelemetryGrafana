import csv
from datetime import datetime
from code.conf_influxdb import *
from code.utils_timestamp import *
from code.damp_ang_to_pos import *


DAMPER_MIN_ANGLE = 0.0
DAMPER_MAX_ANGLE = 100.0
DAMPER_MID_ANGLE = (DAMPER_MAX_ANGLE + DAMPER_MIN_ANGLE) / 2.0

# DEG_TO_MM_FRONT = 1.221374046
# DEG_TO_MM_REAR = 1.070090958
# R_TO_DEG = 100.0
# 100R = 10mm

# linear interpolation
def lerp(a, b, alpha):
  return a + (alpha * (b - a))

R_TO_MM = 0.1
MAX_ADC_VALUE = 4095.0
REF_VAL_FL = 1080.0 /MAX_ADC_VALUE
REF_VAL_FR = 1740.0 /MAX_ADC_VALUE
REF_VAL_RL = 970.0 /MAX_ADC_VALUE
REF_VAL_RR = 1840.0 /MAX_ADC_VALUE

REF_ANGLE_FL = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_FL)
REF_ANGLE_FR = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_FR)
REF_ANGLE_RL = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_RL)
REF_ANGLE_RR = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, REF_VAL_RR)

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

    angle = calc_wheel_position(row)
    point = (
      Point('damp')
      .tag("ID", f'{row["ID"]}')
      .field("angle", angle)
      .time(timestamp)
    )
    points.append(point)
    
    point = (
      Point('damp')
      .tag("ID", f'{row["ID"]}')
      .field("raw_delta", float(int(row["delta"])))
      .time(timestamp)
    )
    #points.append(point)

    if line_count % 5000 == 0:
      write_api.write(bucket=bucket, org=org, record=points)
      points.clear()
    line_count += 1

  endTime = datetime.datetime.now()
  print(f'DAMP: Imported {line_count} rows in {endTime - startTime}')


def calc_wheel_position(row):
  raw_value = float(int(row["delta"]))
  angle_abs = lerp(DAMPER_MIN_ANGLE, DAMPER_MAX_ANGLE, raw_value / 4095)
  angle = 0.0
  position = 0.0

  match int(row["ID"]):
    case 7:
      angle = -(angle_abs - REF_ANGLE_FL)
    case 8:
      angle = angle_abs - REF_ANGLE_FR
    case 11:
      angle = -(angle_abs - REF_ANGLE_RL)
    case 12:
      angle = (angle_abs - REF_ANGLE_RR)
    case 6:
      delta = (REF_VAL_SW - raw_value) * R_TO_DEG_SW

  #print(f'rawvalue = {raw_value}, angle_abs = {angle_abs}, angle = {angle}')

  if int(row["ID"]) != 6:
    if int(row["ID"]) == 7 or int(row["ID"]) == 8:
      try:
        damper_angle_to_pos_low, damper_angle_to_pos_high = find_closest_angles_front(angle)
      except IndexError:
        pass
    elif int(row["ID"]) == 11 or int(row["ID"]) == 12:
      try:
        damper_angle_to_pos_low, damper_angle_to_pos_high = find_closest_angles_back(angle)
      except IndexError:
        pass
    try:
      position = lerp(damper_angle_to_pos_low[0], damper_angle_to_pos_high[0],
                 (angle - damper_angle_to_pos_low[1]) / (damper_angle_to_pos_high[1] - damper_angle_to_pos_low[1]))
    except UnboundLocalError:
      pass
  else:
    position = delta

  return position
