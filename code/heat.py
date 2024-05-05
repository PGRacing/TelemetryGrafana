import csv
import numpy as np
from func_can import *

volumetric_efficiency_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/volumetric_efficiency.csv'

def find_closest(array, value):
    array = np.array(array)
    array = array.astype(float)
    idx = (np.abs(array - value)).argmin()
    return idx

class Heat:
    water_flow = [0, 0.206, 0.350, 0.493, 0.452]  # kg/s
    water_flow_RPM = [0, 2700, 4200, 6200, 9200]
    water_heat_capacity = 4.184  # kJ/(kg*K)
    water_density = 997 # kg/m3

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
                return self.tps_values[i][0]
            
    def calc_heat_radiators(can_file, last_line_match, delta_left, delta_right, timestamp, heat):
        with open(can_file, 'r') as file:
            data = csv.DictReader(file)
            row_counter = 0
            for row in data:
                if (row['arbitration_id'] == '0x609'):
                    if row_counter >= last_line_match:
                        try:
                            float(row['timestamp'])
                        except ValueError as e:
                            continue
                        timestep = abs(timestamp - float(row['timestamp']))
                        if (timestep < 1.):
                            flow_left, flow_right = calc_flow_on_radiators(row['arbitration_id'], row['data'], int(row['error'])) 
                            left_heat = heat.calc_water_heat(delta_left, flow_left, timestep)
                            right_heat = heat.calc_water_heat(delta_right, flow_right, timestep)
                            return left_heat, right_heat, row_counter
                    else:
                        row_counter += 1
            return -1, -1, last_line_match
            
    def calc_water_heat(self, temp_delta, flow):
        if flow != -1.:
            mass_flow = flow/60  * self.water_density/1000 # kg/s
            heat = mass_flow * self.water_heat_capacity * temp_delta # kJ/s
            return heat
        return 0.
    
    
    
