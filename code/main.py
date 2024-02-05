from func_abs import *
from func_damp import *
from func_gps import *
from func_imu import *
from variances import *
import multiprocessing
import datetime

# TODO IMPORTANT try-except/validate lines import better than aborting whole file import

paths = ['C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/23_11_05_Pszczolki/',
         'C:/Users/krzys/Desktop/telemetry/05.11-Pszczolki/',
         "C:/Users/cepek/Politechnika Gdańska/PGRacing Team - Dokumenty/PGRACING TEAM - PROJEKT/Resources/TESTING/05.11.2023 - Pszczółki/Raw data/05.11-Pszczolki/"
         ]

imported_files = 0
var_gps = 0.
var_acc = 0.
var_gyro = 0.
f_gps = list(range(2))
f_acc = list(range(3))
f_gyro = list(range(3))
use_processes = True

def import_influxdb(filepath):
    global var_gyro
    global var_acc
    global var_gps
    
    processes = []
    start = datetime.datetime.now()

    #var_gyro = calc_var_gyro(filepath + 'GPS0101-12.csv', 'gps')
    #var_acc = calc_var_acc(filepath + 'IMU0101-12.csv', 'imu')
    #var_gps = calc_var_gps(filepath + 'IMU0101-12.csv', 'imu')

    for i in range(1, 34):
        if use_processes:
            processes.append(multiprocessing.Process(target=import_file, args=(filepath, i,)))
            processes[-1].start()
        else:            
            import_file(filepath, i)

    for process in processes:
        process.join()
    print(f'Succesfully imported {imported_files} files in {datetime.datetime.now() - start} seconds')


def import_file(filepath, file_num):
    global imported_files
    global f_gps
    global f_acc
    global f_gyro
    # print(f'i = {file_num}')
    try:
        all_gps_problems = import_csv_gps(filepath + 'GPS0101-' + str(file_num) + '.csv', f_gps)
        (start_time, f_gyro) = all_gps_problems
        if start_time == 0:
            print('Start time not set! Skip this iteration.')
            return
        import_csv_abs(filepath + 'ABS0101-' + str(file_num) + '.csv', start_time)
        import_csv_damp(filepath + 'DAMP0101-' + str(file_num) + '.csv', start_time)
        #imu_data = import_csv_imu(filepath + 'IMU0101-' + str(file_num) + '.csv', start_time, f_acc, f_gyro)
        #(f_acc, f_gyro) = imu_data
        imported_files += 1
    except ValueError as e:
        #print(e)
        print(f'Unxepected error while trying to import {filepath.split("/")[-1]}, continue...')


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


# convert_csv_gps_files(path)
if __name__ == "__main__":
    for path in paths:
        if os.path.exists(path):
            import_influxdb(path)
            break
