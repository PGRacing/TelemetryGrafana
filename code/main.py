from code.func_abs import *
from code.func_damp import *
from code.func_gps import *

# TODO IMPORTANT try-except/validate lines import better than aborting whole file import

paths = ["C:/Users/malwi/Documents/MEGA/PG/PGRacingTeam/telemetry_data/23_11_05_Pszczolki/",
        'C:/Users/krzys/Desktop/telemetry/05.11-Pszczolki/',
        "C:/Users/cepek/Politechnika Gdańska/PGRacing Team - Dokumenty/PGRACING TEAM - PROJEKT/Resources/TESTING/05.11.2023 - Pszczółki/Raw data/05.11-Pszczolki/"
]

def import_influxdb(filepath):
    imported_files = 0
    for i in range(1, 34):
        print(f'i = {i}')
        try:
            start_time = import_csv_gps(filepath + 'GPS0101-' + str(i) + '.csv')
            if start_time == 0:
                print('Start time not set! Skip this iteration.')
                continue
            import_csv_abs(filepath + 'ABS0101-' + str(i) + '.csv', start_time)
            import_csv_damp(filepath + 'DAMP0101-' + str(i) + '.csv', start_time)
            imported_files += 1
        except ValueError as e:
            #print(e)
            print(f'Unxepected error while trying to import {filepath.split("/")[-1]}, continue...')
    print(f'Succesfully imported {imported_files} files!')

def convert_csv_gps_files(filepath):
    for i in range(1, 34):
        print(f'i = {i}')
        try:
            start_time = import_csv_gps(filepath + 'GPS0101-' + str(i) + '.csv')
            if start_time == 0:
                print('Start time not set! Skip this iteration.')
                continue
            convert_csv_gps(filepath + 'GPS0101-' + str(i) + '.csv')
        except ValueError as e:
            print(f'Unxepected error while trying to import {filepath.split("/")[-1]}, continue...')

#convert_csv_gps_files(path)
if __name__ == "__main__":
    for path in paths:
        if os.path.exists(path):
            import_influxdb(path)
            break