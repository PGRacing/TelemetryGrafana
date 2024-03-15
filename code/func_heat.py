import csv
import datetime
from conf_influxdb import *


# TODO change filepath 
volumetryc_efficiency_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/volumetric_efficiency.csv'
filepath = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-09 Pszczolki/20240309_134432.csv'

class EngineHeat:
    def __init__(self) -> None:
        self.engine_map = []
        self.map_values = []
        with open(volumetryc_efficiency_path, 'r') as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                self.engine_map.append(row)
        for i in range(1, len(self.engine_map[0])):
            self.map_values.append(self.engine_map[i][0])
        self.heat_to_cooling_system = 0.29
        self.air = 14.7
        self.fuel = 1.2
        self.air_fuel_sum = 15.9
        self.air_desnity = 1.25 # kg/m^3
        self.air_volume_engine = 675. # cm^3
        self.air_volume_cylinder = 0.000225 # m^3
        self.fuel_density = 770. # kg/m^3
        self.air_mass = self.air_desnity*self.air_volume_cylinder # kg
        self.fuel_mass = self.air_mass/self.air_fuel_sum # kg
        self.volume_flowing_through_injector = 0.00025 # m^3/min
        self.mass_flow_through_the_injector = self.volume_flowing_through_injector * self.fuel_density # kg/min
        self.injection_opening_time = self.fuel_mass / self.mass_flow_through_the_injector # min

        
    def get_heat(self, rpm:int, map:int):
        closest_rpm = 13500
        smallest_diff_rpm = 1350
        closest_map = 20
        smallest_diff_map = 20
        closest_map_index = 1

        # TODO solve this shit 
        i = 1
        for value in self.map_values:
            if abs(map - int(value)) < smallest_diff_map:
                closest_map = int(value)
                smallest_diff_map = abs(map - int(value))
                closest_map_index = i
            i += 1

        for row in self.engine_map[1:]:
            if abs(rpm - int(row[0])) < smallest_diff_rpm:
                closest_rpm = int(row[0])
                smallest_diff_rpm = abs(rpm - int(row[0]))
        
        for row in self.engine_map[1:]:
            if int(row[0]) == closest_rpm:
                volumetric_eff = float(row[closest_map_index])

        heat = (volumetric_eff/100 * self.injection_opening_time * self.mass_flow_through_the_injector) * (((closest_rpm * 3/2))/60) * 43000 * self.heat_to_cooling_system 

        #print(f'rpm: {closest_rpm}, map: {closest_map}, volumetric efficiency: {volumetric_eff}, heat: {heat}')

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
                Point('cooling')
                .tag("engine", 'to_cooling')
                .field("heat2", heat)
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('cooling')
                .tag("engine", 'to_cooling')
                .field("MAP", int(row['MAP']))
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('cooling')
                .tag("engine", 'to_cooling')
                .field("RPM", int(row['RPM']))
                .time(timestamp)
            )
            points.append(point)

            point = (
                Point('cooling')
                .tag("engine", 'to_cooling')
                .field("TPS", int(row['TPS']))
                .time(timestamp)
            )
            points.append(point)

            if row_counter % 1200 == 0:
                write_api.write(bucket=bucket, org=org, record=points)
                points.clear()
            row_counter += 1

        write_api.write(bucket=bucket, org=org, record=points)
        print('END OF X FILE')


engine_heat = EngineHeat()
import_csv_heat(filepath)


