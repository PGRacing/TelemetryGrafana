import csv
import datetime
import numpy as np
from conf_influxdb import *

volumetric_efficiency_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/volumetric_efficiency.csv'
path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-09 Pszczolki/ecumaster/'
cooling_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-09 Pszczolki/cooling/'
cooling_first_matching_hour = 'cooling_system_temp_12_29_42.csv'


def find_closest(array, value):
    array = np.array(array)
    array = array.astype(float)
    idx = (np.abs(array - value)).argmin()
    return idx


class EngineHeat:
    water_flow = [0, 0.206, 0.350, 0.493, 0.452]  # kg/s
    water_flow_RPM = [0, 2700, 4200, 6200, 9200]
    water_heat_capacity = 4.184  # kJ/(kg*K)

    def __init__(self) -> None:
        self.engine_map = []
        self.map_values = []
        self.tps_values = []
        for i in range(10, 101, 10):
            self.tps_values.append([i, 0])
        self.tps_values_percentage = []
        for i in range(10, 101, 10):
            self.tps_values_percentage.append([i, 0])
        with open(volumetric_efficiency_path, 'r') as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                self.engine_map.append(row)
        for i in range(1, len(self.engine_map[0])):
            self.map_values.append(self.engine_map[0][i])
        self.rpm_values = [x[0] for x in self.engine_map[1:]]
        self.heat_to_cooling_system = 0.29
        self.air = 14.7
        self.fuel = 1.2
        self.air_fuel_sum = 15.9
        self.air_desnity = 1.25  # kg/m^3
        self.air_volume_engine = 675.  # cm^3
        self.air_volume_cylinder = 0.000225  # m^3
        self.fuel_density = 770.  # kg/m^3
        self.air_mass = self.air_desnity * self.air_volume_cylinder  # kg
        self.fuel_mass = self.air_mass / self.air_fuel_sum  # kg
        self.volume_flowing_through_injector = 0.00025  # m^3/min
        self.mass_flow_through_the_injector = self.volume_flowing_through_injector * self.fuel_density  # kg/min
        self.injection_opening_time = self.fuel_mass / self.mass_flow_through_the_injector  # min

    def get_heat(self, rpm: int, map: int):
        closest_map_index = int(find_closest(self.map_values, map))
        closest_rpm_index = int(find_closest(self.rpm_values, rpm))
        volumetric_eff = float(self.engine_map[closest_rpm_index][closest_map_index])
        closest_rpm = float(self.rpm_values[closest_rpm_index])

        heat = (volumetric_eff / 100.0 * self.injection_opening_time * self.mass_flow_through_the_injector) * (
                    (closest_rpm * 3 / 2) / 60) * 43000 * self.heat_to_cooling_system


        # print(f'rpm: {closest_rpm}, map: {closest_map}, volumetric efficiency: {volumetric_eff}, heat: {heat}')

        return heat

    def get_telemetry_engine_heat(self, rpm, engine_temp_delta):
        if rpm == 0 or engine_temp_delta <= 0 :
            return 0
        interpolated_water_flow = np.interp(rpm, self.water_flow_RPM, self.water_flow)
        heat = engine_temp_delta * interpolated_water_flow * self.water_heat_capacity
        return heat
    
    def update_tps_list(self, tps):
        for i in range(len(self.tps_values)):
            if tps <= self.tps_values[i][0]:
                self.tps_values[i][1] += 1
                break

    
    def calc_tps_values_percentage(self):
        number_of_records = 0
        for pair in self.tps_values:
            number_of_records += pair[1]
        for i in range(len(self.tps_values_percentage)):
            self.tps_values_percentage[i][1] = self.tps_values[i][1]/number_of_records*100
        self.tps_values_percentage[9][0] = 99

    def match_range(self, tps):
        for i in range(len(self.tps_values)):
            if tps <= self.tps_values[i][0]:
                self.tps_values[i][1] += 1
                #print(self.tps_values[i][0])
                return self.tps_values[i][0]


def find_start_time(filename):
    year = int(filename[:4])
    month = int(filename[4:6])
    day = int(filename[6:8])
    hour = int(filename[9:11])# - 1
    if hour == -1:
        day -= 1
        hour = 23
    minute = int(filename[11:13])
    second = int(filename[13:15])
    start_time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    return start_time

def find_first_closest_record(timestamp):
    for item in os.listdir(cooling_path):
        #full_path = os.path.join(cooling_path, item)
        #if os.path.isfile(full_path) and item.endswith('.csv'):
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
            second = float(row['TIME'].replace(',', '.'))
            seconds_timedelta = datetime.timedelta(seconds=second)
            timestamp = start_time + seconds_timedelta
            ecumaster_timestamp = timestamp.timestamp() #- 3600. # in seconds
            timestamp_grafana = timestamp - datetime.timedelta(hours=1)

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
    engine_heat = EngineHeat()
    cooling_list = list_cooling_system_files(cooling_path) 
    find_files(path, cooling_list, engine_heat)
    print(engine_heat.tps_values)
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


