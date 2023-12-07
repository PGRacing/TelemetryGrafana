import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *
import struct

def import_csv_ecu(filepath):
  # CSV column names as following:
  # timestamp,ID,speed
  # date like '2023-11-04'
  file = open(filepath, "rb")
  line_count = 0
  points = []
  startTime = datetime.datetime.now()

  msg_bytes = 44
  timestamp_bytes = 4
  timestamp_mod = 1000

  while True:
    while True:
      if file.read(1) == b',':
        break
    # read timestamp
    #timestamp = file.read(timestamp_bytes)
    #if (int(timestamp) + 1) >= timestamp_mod:
    #  timestamp_bytes += 1
    #  timestamp_mod *= 10
    # read comma
    file.read(1)
    str_line = ''
    chunk = file.read(44)
    telemetry_data = struct.unpack('HBBHHHBBBhbBBBHHBbHHBBBHBBBf', chunk)
    #for i in range(44):
      #str_line += f'{ord(file.read(1))},'
      #print(f'{ord(file.read(1))}')
    #row_bin = file.read(msg_bytes)
    # read newline char
    file.read(2)
    if line_count == 1000:
      break
    #print(f'{row_bin}')
    line_count += 1
    #print(str_line)
    #print(timestamp)
    print(telemetry_data)

  endTime = datetime.datetime.now()
  print(f'ECU: Imported {line_count} rows in {endTime - startTime}')