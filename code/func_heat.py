import csv


# TODO change filepath 
volumetryc_efficiency_path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-03 Pszczolki/racebox/'

class EngineHeat:
    def __init__(self) -> None:
        with open(volumetryc_efficiency_path, 'r') as file:
            self.engine_map = csv.DictReader(file)
        self.heat_to_cooling_system = 0.29
        self.air = 14.7
        self.fuel = 1.2
        self.air_fuel_sum = 15.9
        self.air_desnity = 1.25 # kg/m^3
        self.air_volume_engine = 675. # cm^3
        self.air_volume_cylinder = 0.000225 # m^3
        self.fuel_density = 770. # kg/m^3
        self.air_mass = self.air_desnity/self.air_volume_cylinder # kg
        self.fuel_mass = self.air_mass/self.air_fuel_sum # kg
        self.volume_flowing_through_injector = 0.00025 # m^3/min
        self.mass_flow_through_the_injector = self.volume_flowing_through_injector * self.fuel_density # kg/min
        self.injection_opening_time = self.fuel_mass / self.mass_flow_through_the_injector # min

        
    def get_heat(self, rpm:int, map:int):
        closest_rpm = 13500
        smallest_diff_rpm = 1350
        closest_map = 20
        smallest_diff_map = 20
        map_values = self.engine_map.keys()

        for value in map_values:
            if abs(map - int(value)) < smallest_diff_map:
                closest_map = int(value)
                smallest_diff_map = abs(map - int(value))

        for row in self.engine_map:
            if abs(rpm - int(row['rpm'])) < smallest_diff_rpm:
                closest_rpm = int(row['rpm'])
                smallest_diff_rpm = abs(rpm - int(row['rpm']))
        
        for row in self.engine_map:
            if int(row['rpm']) == closest_rpm:
                volumetric_eff = float(row[f'{closest_map}'])

        heat = (volumetric_eff/100 * self.injection_opening_time * self.mass_flow_through_the_injector) * (((int(row['rpm']) * 3/2))/60) * 43000 * self.heat_to_cooling_system 

        return heat






