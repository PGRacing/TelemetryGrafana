import csv
import operator
from datetime import datetime
from functools import reduce
from conf_influxdb import *
from utils_timestamp import *
from kalman_filters import *
from lap_timer import *

lap_counter = 0
last_time = 0.
best_lap_number = 0
best_time = 0.

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

def import_csv_gps(filepath, f_gps):
    global lap_counter
    global best_lap_number
    global best_time
    global last_time
    # CSV column names as following:
    # timestamp,LOG,utc,pos status,lat,lat dir,lon,lon dir,speed,track,date,mag var,var dir,mode ind,chs,ter
    # date like '2023-11-04'
    file = open(filepath, "r")
    csv_reader = csv.DictReader(file)
    line_count = 0
    start_time = 0
    points = []
    #coefficients = [['00:00:00:000', 0.9489]]
    new_row = ''
    startTime = datetime.now()
    lap_timer = LapTimer()
    previous_timestamp = None
    previous_csv_timestamp = None

    for row in csv_reader:
        date = True
        if row['date']:
            try:
                float(row["date"])
            except ValueError:
                date = False

        if row["timestamp"] and date and row["date"]:
            #start_timestamp = str(correct_gp_start_time(row['timestamp']))
            start_time = gps_timestamp_sub_timestamp(row["date"], row["utc"], row["timestamp"])
            break

    if start_time == 0:
        return 0, f_gps#, coefficients
  #print(start_time)

    for row in csv_reader:
        #print(f'{row["timestamp"]}; {row["LOG"]}; {row["utc"]}; {row["pos status"]}; {row["lat"]}; {row["lat dir"]}; {row["lon"]}; {row["lon dir"]}; {row["speed"]}; {row["track"]}; {row["date"]}; {row["mode ind"]}')
        if row["lat"] and row["lat dir"] and row["lon"] and row["lon dir"]:
            new_row = f'{row["LOG"]},{row["utc"]},{row["pos status"]},{row["lat"]},{row["lat dir"]},{row["lon"]},{row["lon dir"]},{row["speed"]},{row["track"]},{row["date"]},{row["mag var"]},{row["var dir"]},{row["mode ind"]},{row["chs"]}\n'
            if not nmea_checksum(new_row):
                continue
        else:
            #print(f'{row["lat"]}, {row["lat dir"]}, {row["lon"]}, {row["lon dir"]},')
            continue
    
        org_timestamp = row["timestamp"]
        timestamp = start_time_add_timestamp(start_time, org_timestamp)
        
        #if line_count < 1:
            #init_time = csv_timestamp_to_timedelta(row["timestamp"])
            #first_timestamp = correct_init_time(init_time)
            #timestamp = start_time + first_timestamp
            #prev_timestamp = row['timestamp']
            #prev_utc = row['utc']
            #coefficient = 0.9496
            #coefficients.append([row['timestamp'], coefficient])
        #else:
            #if line_count % 300 == 0:
                #coefficient = set_new_coefficient(prev_utc, row['utc'], prev_timestamp, row['timestamp'])
                #prev_timestamp = row['timestamp']
                #prev_utc = row['utc']
                #coefficients.append([row['timestamp'], coefficient])
            #timestamp = correct_csv_timestamp(previous_csv_timestamp, row["timestamp"], previous_timestamp, coefficient)
        #previous_timestamp = timestamp
        #previous_csv_timestamp = org_timestamp



        # transformation x1 = int(x/100) + ((x%100)/60)
        lat = (float(row["lat"]) / 100 // 1) + (float(row["lat"]) % 100.0 / 60.0)
        lon = (float(row["lon"]) / 100 // 1) + (float(row["lon"]) % 100.0 / 60.0)

        f_gps = kalman_gps(f_gps, lat, lon, line_count)

        if line_count == 0:
            lap_timer.init_position(x=f_gps[1].x[0][0], y=f_gps[0].x[0][0], time=timestamp)
        else:
            last_time, lap_diff, inner_lap_counter = lap_timer.check(x=f_gps[1].x[0][0], y=f_gps[0].x[0][0], timestamp=timestamp)
            lap_counter += lap_diff
        if (last_time < best_time and inner_lap_counter != 0) or lap_counter == 1:
                best_time = last_time
                best_lap_number = lap_counter

        point = (
            Point('gps')
            .tag("ID", "gps_position")
            .field("latitude", f_gps[0].x[0])
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('gps')
            .tag("ID", "gps_position")
            .field("longitude", f_gps[1].x[0])
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('gps')
            .tag("ID", "gps_position")
            .field("speed", float(row["speed"]) * 1.852)
            .time(timestamp)
        )
        points.append(point)
        point = (
            Point('lap_times')
            .tag("lap_time", 'last')
            .field("last_time", last_time)
            .time(timestamp)
        )
        points.append(point)

        point = (
            Point('lap_times')
            .tag('lap_time', 'best')
            .field('best_time', best_time)
            .time(timestamp)
        )
        points.append(point)

        point = (
            Point('lap_times')
            .tag('lap_time', 'best_lap_number')
            .field('best_lap_number', best_lap_number)
            .time(timestamp)
        )
        points.append(point)

        point = (
            Point('lap_times')
            .tag('lap_time', 'lap_number')
            .field('lap_counter', lap_counter)
            .time(timestamp)
        )
        points.append(point)
        if line_count % 1666 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        line_count += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.now()
    print(f'GPS: Imported {line_count} rows in {endTime - startTime}')

    file.close()

    return start_time, f_gps

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


  '''
  live telemetry.
  '''

def gps_data(queue, filter):
      
    # TODO: decode data

    lat = (float(lat) / 100 // 1) + (float(lat) % 100.0 / 60.0)
    lon = (float(lon) / 100 // 1) + (float(lon) % 100.0 / 60.0)

    if lat and lon:
        filter.filter_gps(lat, lon, False)
    else:
        filter.filter_gps(0, 0, True)

    data_to_send = {
        "lat": filter[0].x[0][0],
        "lon": filter[1].x[0][0],
    }

    return data_to_send
      