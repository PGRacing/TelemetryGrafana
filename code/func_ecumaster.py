import csv
import datetime
import numpy as np
from conf_influxdb import *
from heat import *
from func_temp_cooling_sys import *


path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-05-14 Pszczolki/ecumaster/'
cooling_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-05-14 Pszczolki/cooling/'
cooling_first_matching_hour = 'cooling_system_temp_16_07_58.csv'


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
    theoretical_heat_prev = 0
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
                '''
                Make a proper timestamp
                '''
                second = float(row['TIME'].replace(',', '.'))
                seconds_timedelta = datetime.timedelta(seconds=second)
                timestamp = start_time + seconds_timedelta
                ecumaster_timestamp = timestamp.timestamp() #- 3600. # in seconds
                timestamp_grafana = timestamp - datetime.timedelta(hours=2)

                '''
                Calculate heat (excel) and derivative of a function and find tps range
                '''

                theoretical_heat = engine_heat.get_heat(int(row['RPM']), int(row['MAP']))
                derivative_theoretical = calc_derivative(theoretical_heat, theoretical_heat_prev, 0.04)
                tps_range = engine_heat.match_range(int(row['TPS']))

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
                    .field("heat_theoretical_new_map", theoretical_heat)
                    .time(timestamp_grafana)
                )
                points.append(point)

                point = (
                    Point('engine')
                    .tag("engine", 'heat')
                    .field("derivative", derivative_theoretical)
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
                theoretical_heat_prev = theoretical_heat

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




'''

For logger reading.

'''

def engine_data1(data, timestamp, theoretical_heat_prev, points):

    # TODO deocde bytes
    '''
    <   Little Endian Byte Order
    H   unsigned 16 bits
    B   unsigned 8 bits
    b   signed 8 bits
    '''
    rpm, tps, iat, map, injpw = struct.unpack('<HBbHH', data)
    tps *= 0.5

    theoretical_heat = engine_heat.get_heat(rpm, map)
    derivative_theoretical = calc_derivative(theoretical_heat, theoretical_heat_prev, 0.04)
    tps_range = engine_heat.match_range(tps)

    point = (
        Point('engine')
        .tag("value", 'range')
        .field("TPS", tps_range)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('engine')
        .tag("engine", 'heat')
        .field("theoretical_heat", theoretical_heat)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('engine')
        .tag("engine", 'heat')
        .field("theoretical_growth", derivative_theoretical)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('engine')
        .tag("engine", 'raw')
        .field("MAP", map)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('engine')
        .tag("engine", 'raw')
        .field("RPM", rpm)
        .time(timestamp)
    )
    points.append(point)


    point = (
        Point('engine')
        .tag("engine", 'raw')
        .field("TPS", tps)
        .time(timestamp)
    )
    points.append(point)

    return theoretical_heat


def engine_data2(data, timestamp, points):

    vspd, baro, oil_temperature, oil_preassure, fuelp, clt = struct.unpack('<HBBBBh', data)
    clt -= 40
    oil_preassure *= 0.0625

    point = (
        Point('engine')
        .tag("oil", 'raw')
        .field("oil_temperature", oil_temperature)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('engine')
        .tag("oil", 'raw')
        .field("oil_preassure", oil_preassure)
        .time(timestamp)
    )
    points.append(point)

    point = (
        Point('engine')
        .tag("ecumaster", 'raw')
        .field("CLT", clt)
        .time(timestamp)
    )
    points.append(point)

    return clt

def engine_data6(data, timestamp, points):

    ain5, ain6, outflags1, outflags2, outflags3, outflags4 = struct.unpack('<HHBBBB', data)
    outflags4_bits = ((outflags4 >> bit) & 1 for bit in range(8))
    (fps, coolant_fan, ac_clutch, ac_fan, nitrous, starter_req, boost_map_state) = outflags4_bits

    point = (
        Point('engine')
        .tag("engine", 'raw')
        .field("coolant_fan", coolant_fan)
        .time(timestamp)
    )
    points.append(point)


'''
LIve telemetry.
'''
def engine_data0_live(queue, theoretical_heat_prev):
    '''
    <   Little Endian Byte Order
    H   unsigned 16 bits
    B   unsigned 8 bits
    b   signed 8 bits
    '''
    data = bytearray()
    for i in range(8):
        data.extend([queue.get()])

    rpm, tps, iat, map, injpw = struct.unpack('<HBbHH', data)
    tps *= 0.5

    theoretical_heat = engine_heat.get_heat(rpm, map)
    derivative_theoretical = calc_derivative(theoretical_heat, theoretical_heat_prev, 0.04)
    tps_range = engine_heat.match_range(tps)

    data_to_send = {
        "RPM": rpm,
        "TPS": tps,
        "MAP": map,
        "theoretical_heat": theoretical_heat,
        "theoretical_growth": derivative_theoretical,
        "iat": iat,
    }
    return data_to_send


def engine_data2_live(queue):
    data = bytearray()
    for i in range(8):
        data.extend([queue.get()])

    vspd, baro, oil_temperature, oil_pressure, fuelp, clt = struct.unpack('<HBBBBh', data)
    clt -= 40
    oil_preassure *= 0.0625

    data_to_send = {
        "CLT": clt,
        "oil_temperature": oil_temperature,
        "oil_pressure": oil_pressure,

    }
    return data_to_send

def engine_data3_live(queue):
    data = bytearray()
    for i in range(8):
        data.extend([queue.get()])

    ignang, dwell, lambda_, lamcorr, egt1, egt2 = struct.unpack('<bBBBHH', data)
    lambda_ *= 0.0078125

    data_to_send = {
        "lambda": lambda_,

    }
    return data_to_send

def engine_data4_live(queue):
    data = bytearray()
    for i in range(8):
        data.extend([queue.get()])

    gera, ecu_temp, batt, errflag, flags1, ethanol_content = struct.unpack('<BbHBBB', data)
    batt *= 0.027

    flags1_bits = ((flags1 >> bit) & 1 for bit in range(8))
    (gearcut, als, lc, idle, table_set, tc_intervention, pit_limiter) = flags1_bits

    data_to_send = {
        "lambda": batt,
        "gearcut": gearcut,
        "als": als,
        "lc": lc,
        "idle": idle,
        "table_set": table_set,
        "tc_intervention": tc_intervention,
        "pit_limiter": pit_limiter,

    }
    return data_to_send

def engine_data6_live(queue):
    data = bytearray()
    for i in range(8):
        data.extend([queue.get()])

    ain5, ain6, outflags1, outflags2, outflags3, outflags4 = struct.unpack('<HHBBBB', data)
    outflags4_bits = ((outflags4 >> bit) & 1 for bit in range(8))
    (fps, coolant_fan, ac_clutch, ac_fan, nitrous, starter_req, boost_map_state) = outflags4_bits

    data_to_send = {
        "coolant_fan": coolant_fan,

    }
    return data_to_send

def fuel_data(data, timestamp):

    #TODO decode bytes

    data_to_send = {
        "timestamp": timestamp,
        "fuel_consumption": fuel_consumption,
        "burned_fuel": burned_fuel,

    }
    return data_to_send
    

if __name__ == "__main__":
    engine_heat = Heat()
    cooling_list = list_cooling_system_files(cooling_path) 
    find_files(path, cooling_list, engine_heat)
