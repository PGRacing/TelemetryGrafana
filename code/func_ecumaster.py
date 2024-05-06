import csv
import datetime
import numpy as np
from conf_influxdb import *
from heat import *


path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-04-30 proto - test can/ecumaster/'
cooling_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-04-30 proto - test can/cooling/'
cooling_first_matching_hour = 'cooling_system_temp_23_55_48.csv'


def find_start_time(filename):
    year = int(filename[:4])
    month = int(filename[4:6])
    day = int(filename[6:8])
    hour = int(filename[9:11])
    minute = int(filename[11:13])
    second = int(filename[13:15])
    start_time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    return start_time

def find_first_closest_record(timestamp):
    for item in os.listdir(cooling_path):
        engine_delta = open_file_find_value(item, timestamp)
        if engine_delta == -1000:
            continue
        else:
            return engine_delta, item

                    
def find_closest_record(timestamp, last_used_file, last_file_index, cooling_list):
    engine_delta = open_file_find_value(last_used_file, timestamp)
    if engine_delta == -1000:
        for index in range(len(cooling_list)):
            new_file = cooling_list[index]
            last_used_file = new_file
            engine_delta = open_file_find_value(last_used_file, timestamp)
            if engine_delta != -1000.0:
                break
            
    return engine_delta, last_used_file
    

def open_file_find_value(filename, timestamp):
    with open(cooling_path + filename, 'r') as file:
        data = csv.DictReader(file)
        for row in data:
            try:
                # delta between cooling and ecumaster timestamp
                time_delta = abs(float(row['timestamp']) - timestamp)
                if time_delta < 1.:
                    engine_delta = float(row['engine_out']) - float(row['engine_in'])
                    if engine_delta < -90.:
                        print(row)
                        print(filename)
                        print(time_delta)
                    return engine_delta
            except ValueError as e:
                continue
    # -1000 when no match found
    return -1000

def find_first_cooling_timestamp():
    #min_time_diff = 2000.
    #for item in os.listdir(cooling_path):
    with open(cooling_path + cooling_first_matching_hour, 'r') as file:
        data = csv.DictReader(file)
        for row in data:
            first_timestamp = float(row['timestamp'])
            break

    return first_timestamp


def import_csv_heat(filepath, engine_heat, cooling_list, file_counter):
    global LAST_TIMESTAMP
    row_counter = 0
    first_match_row_number = 0
    #engine_heat = EngineHeat()
    points = []
    split_path = filepath.split("/")
    filename = split_path[-1]
    last_used_file = ''
    start_time = find_start_time(filename)
    seconds_start_time = start_time.timestamp()
    first_timestamp_match = False
    #first_coling_timestamp_match = False

    for idx in range(len(cooling_list)):
        if cooling_list[idx] == cooling_first_matching_hour:
            file_index = idx
    print(f'current ecumaster file: {filename}')
    print(f'matching cooling system file: {cooling_list[file_index+file_counter-1]}')

    first_cooling_timestamp = find_first_cooling_timestamp()

    with open(filepath, 'r') as file:
        data = csv.DictReader(file, delimiter=';')

        for row in data:
            if (float(row['MAP']) != 0 and float(row['CLT']) != 0):
                second = float(row['TIME'].replace(',', '.'))
                seconds_timedelta = datetime.timedelta(seconds=second)
                timestamp = start_time + seconds_timedelta
                ecumaster_timestamp = timestamp.timestamp() #- 3600. # in seconds
                timestamp_grafana = timestamp - datetime.timedelta(hours=2)

                if not first_timestamp_match:
                    diff = abs(ecumaster_timestamp - first_cooling_timestamp)
                    if diff < 1.1:
                        first_match_row_number = row_counter
                        engine_delta, last_used_file = find_first_closest_record(first_cooling_timestamp)
                        first_timestamp_match = True


                theoretical_heat = engine_heat.get_heat(int(row['RPM']), int(row['MAP']))
                #engine_heat.update_tps_list(int(row['TPS']))
                tps_range = engine_heat.match_range(int(row['TPS']))

                #if (row_counter + first_match_row_number) % 25 == 0:
                    #print('podzielne linijki')
                # 1 second passes
                if first_timestamp_match and (row_counter + first_match_row_number) % 25 == 0:
                    # find proper values from cooling systam data
                    engine_delta, last_used_file = find_closest_record(ecumaster_timestamp, last_used_file, file_index+file_counter-1, cooling_list)
                    heat_from_engine = engine_heat.get_telemetry_engine_heat(int(row['RPM']), engine_delta)
                    if heat_from_engine < 0:
                        print('ERROR, heat less than 0')
                        print(engine_delta)
                        #print()

                    point = (
                        Point('engine')
                        .tag("engine", 'heat')
                        .field("heat_from_engine", float(heat_from_engine))
                        .time(timestamp_grafana)
                    )
                    points.append(point)

                point = (
                    Point('engine')
                    .tag("value", 'range')
                    .field("TPS", tps_range)
                    .time(timestamp_grafana)
                )
                points.append(point)

                point = (
                    Point('engine')
                    .tag("engine", 'heat')
                    .field("heat_theoretical", theoretical_heat)
                    .time(timestamp_grafana)
                )
                points.append(point)

                point = (
                    Point('engine')
                    .tag("engine", 'raw')
                    .field("MAP", int(row['MAP']))
                    .time(timestamp_grafana)
                )
                points.append(point)

                point = (
                    Point('engine')
                    .tag("engine", 'raw')
                    .field("RPM", int(row['RPM']))
                    .time(timestamp_grafana)
                )
                points.append(point)

                point = (
                    Point('engine')
                    .tag("engine", 'raw')
                    .field("TPS", int(row['TPS']))
                    .time(timestamp_grafana)
                )
                points.append(point)

                try:
                    point = (
                        Point('engine')
                        .tag("engine", 'raw')
                        .field("Coolant fan", int(row['Coolant fan']))
                        .time(timestamp_grafana)
                    )
                    points.append(point)
                except KeyError as e:
                    pass
                    
                try:
                    point = (
                        Point('engine')
                        .tag("oil", 'raw')
                        .field("temp", int(row['Oil temperature']))
                        .time(timestamp_grafana)
                    )
                    points.append(point)
                except KeyError as e:
                    pass

                try:
                    point = (
                        Point('engine')
                        .tag("ecumaster", 'raw')
                        .field("clt", int(row['CLT']))
                        .time(timestamp_grafana)
                    )
                    points.append(point)
                except KeyError as e:
                    pass

                if row_counter % 900 == 0:
                    write_api.write(bucket=bucket, org=org, record=points)
                    points.clear()
                row_counter += 1

        LAST_TIMESTAMP = timestamp_grafana
        write_api.write(bucket=bucket, org=org, record=points)
        print(f'Succesfully send data from {filename}')

def find_files(path, cooling_list, engine_heat):
    file_counter = 0
    startProgram = datetime.datetime.now()
    for item in os.listdir(path):
        full_path = os.path.join(path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            file_counter += 1
            import_csv_heat(full_path, engine_heat, cooling_list, file_counter)
    endProgram = datetime.datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram-startProgram}!')

def list_cooling_system_files(path):
    files_list = []
    for item in sorted(os.listdir(path)):
        files_list.append(item)
    return files_list

def find_match(seconds):
    for item in os.listdir(cooling_path):
        with open(cooling_path + item, 'r') as file:
            data = csv.DictReader(file)
            for row in data:
                if row['timestamp'].startswith(seconds):
                    print(item)
                    break

if __name__ == "__main__":
    #scnds = '1710614428'
    #find_match(scnds)
    #LAST_TIMESTAMP = None
    engine_heat = Heat()
    cooling_list = list_cooling_system_files(cooling_path) 
    find_files(path, cooling_list, engine_heat)
    #print(engine_heat.tps_values)
    #points = []
    #engine_heat.calc_tps_values_percentage()
    #for i in range(len(engine_heat.tps_values_percentage)):
        #point = (
            #Point('engine')
            #.tag("TPS", f'{engine_heat.tps_values_percentage[i][0]}%')
            #.field("TPS_percentage", float(engine_heat.tps_values_percentage[i][1]))
            #.time(LAST_TIMESTAMP)
        #)
        #points.append(point)
    #write_api.write(bucket=bucket, org=org, record=points)


