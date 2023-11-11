import csv
import operator
from datetime import datetime
from functools import reduce
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

def byte_xor_row(row):
  row_list = list(row.values())
  row_list[0] = int.from_bytes(str.encode(row_list[0]), byteorder='big')
  for i in range(1, len(row_list)-1):
    e1 = row_list[i-1]
    e2 = int.from_bytes(str.encode(row_list[i]), byteorder='big')
    row_list[i] = e1 ^ e2
  return row_list[-2].to_bytes(length=len(row["chs"]), byteorder='big')

def nmea_checksum(sentence: str):
    # Checks the validity of an NMEA string using it's checksum
    try:
      sentence = sentence.strip("$\n")
      nmeadata, checksum = sentence.split("*", 1)
      calculated_checksum = reduce(operator.xor, (ord(s) for s in nmeadata), 0)
      if int(checksum, base=16) == calculated_checksum:
          return True
      else:
          return False
    except ValueError as e:
       return False

def convert_csv_gps(filepath):
  # convert csv data to csv in standard for eg. gpsvisualizer.com
  # CSV column names as following:
  # timestamp,LOG,utc,pos status,lat,lat dir,lon,lon dir,speed,,track,date,,mag var,var dir,mode ind,chs,ter
  # date like '2023-11-04'
  file = open(filepath, "r")
  savefile = open(f'{filepath[:-4]}-gpsvisu.csv', "w")
  csv_reader = csv.DictReader(file)
  removed_lines = 0
  new_row = ''

  for row in csv_reader:
    #print(f'{row["timestamp"]}; {row["LOG"]}; {row["utc"]}; {row["pos status"]}; {row["lat"]}; {row["lat dir"]}; {row["lon"]}; {row["lon dir"]}; {row["speed"]}; {row["track"]}; {row["date"]}; {row["mode ind"]}')
    if row["lat"] and row["lat dir"] and row["lon"] and row["lon dir"]:
        new_row = f'{row["LOG"]},{row["utc"]},{row["pos status"]},{row["lat"]},{row["lat dir"]},{row["lon"]},{row["lon dir"]},{row["speed"]},{row["track"]},{row["date"]},{row["mag var"]},{row["var dir"]},{row["mode ind"]},{row["chs"]}\n'
        if nmea_checksum(new_row):
          savefile.write(new_row)
        else:
           removed_lines += 1
  savefile.close()
  print(f'Removed {removed_lines} lines with wrong checksum from {filepath.split("/")[-1]}')