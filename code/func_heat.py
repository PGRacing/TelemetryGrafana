import csv
import datetime
import numpy as np
from code.conf_influxdb import *

# TODO change filepath
volumetric_efficiency_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/volumetric_efficiency.csv'
filepath = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-09 Pszczolki/20240309_134432.csv'
path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-17 Pszczolki/ecumaster/'


def find_closest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


class EngineHeat:
    water_flow = [0, 0.206, 0.350, 0.493, 0.452]  # kg/s
    water_flow_RPM = [0, 2700, 4200, 6200, 9200]
    water_heat_capacity = 4.184  # kJ/(kg*K)

    def __init__(self) -> None:
        self.engine_map = []
        self.map_values = []
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
        closest_map_index = find_closest(self.map_values, map)
        closest_rpm_index = find_closest(self.rpm_values, rpm)
        volumetric_eff = float(self.engine_map[closest_rpm_index][closest_map_index])
        closest_rpm = float(self.rpm_values[closest_rpm_index])

        heat = (volumetric_eff / 100.0 * self.injection_opening_time * self.mass_flow_through_the_injector) * (
                    (closest_rpm * 3 / 2) / 60) * 43000 * self.heat_to_cooling_system


        # print(f'rpm: {closest_rpm}, map: {closest_map}, volumetric efficiency: {volumetric_eff}, heat: {heat}')

        return heat

    def get_telemetry_engine_heat(self, rpm, engine_temp_delta):
        if rpm == 0 or engine_temp_delta == 0:
            return 0
        interpolated_water_flow = np.interp(rpm, self.water_flow_RPM, self.water_flow)
        heat = engine_temp_delta * interpolated_water_flow * self.water_heat_capacity
        return heat


def import_csv_heat(filepath):
    row_counter = 0
    engine_heat = EngineHeat()
    points = []
    path = filepath.split("/")
    filename = path[-1]
    year = int(filename[:4])
    month = int(filename[4:6])
    day = int(filename[6:8])
    hour = int(filename[9:11]) - 1
    if hour == -1:
        day -= 1
        hour = 23
    minute = int(filename[11:13])
    second = int(filename[13:15])
    start_time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    with open(filepath, 'r') as file:
        data = csv.DictReader(file, delimiter=';')

        for row in data:
            second = float(row['TIME'].replace(',', '.'))
            heat = engine_heat.get_heat(int(row['RPM']), int(row['MAP']))
            seconds_timedelta = datetime.timedelta(seconds=second)
            timestamp = start_time + seconds_timedelta

            point = (
                Point('engine')
                .tag("engine", 'heat')
                .field("heat3", heat)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('engine')
                .tag("engine", 'raw')
                .field("MAP", int(row['MAP']))
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('engine')
                .tag("engine", 'raw')
                .field("RPM", int(row['RPM']))
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('engine')
                .tag("engine", 'raw')
                .field("TPS", int(row['TPS']))
                .time(timestamp)
            )
            points.append(point)

            try:
                point = (
                    Point('engine')
                    .tag("engine", 'raw')
                    .field("Coolant fan", int(row['Coolant fan']))
                    .time(timestamp)
                )
                points.append(point)
            except KeyError as e:
                pass
                
            try:
                point = (
                    Point('engine')
                    .tag("oil", 'raw')
                    .field("temp", int(row['Oil temperature']))
                    .time(timestamp)
                )
                points.append(point)
            except KeyError as e:
                pass

            try:
                point = (
                    Point('engine')
                    .tag("ecumaster", 'raw')
                    .field("clt", int(row['CLT']))
                    .time(timestamp)
                )
                points.append(point)
            except KeyError as e:
                pass

            if row_counter % 900 == 0:
                write_api.write(bucket=bucket, org=org, record=points)
                points.clear()
            row_counter += 1

        write_api.write(bucket=bucket, org=org, record=points)
        print(f'Succesfully send data from {filename}')

def find_files(path):
    file_counter = 0
    startProgram = datetime.datetime.now()
    for item in os.listdir(path):
        full_path = os.path.join(path, item)

        if os.path.isfile(full_path) and item.endswith('.csv'):
            file_counter += 1
            import_csv_heat(full_path)
    endProgram = datetime.datetime.now()
    print(f'Successfully imported {file_counter} files in {endProgram-startProgram}!')


if __name__ == "__main__":
    engine_heat = EngineHeat()
    find_files(path)
