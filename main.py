import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from conf_influxdb import *
from func_damp import *
from func_abs import *
from func_gps import *

path = 'C:/Users/krzys/Desktop/telemetry/5.11.2023/'

for i in range(1, 15):
    print(f'i = {i}')
    start_time = import_csv_gps(path + 'GPS0101-' + str(i) + '.csv')
    if start_time == 0:
        print('Start time not set! Skip this iteration.')
        continue
    import_csv_abs(path + 'ABS0101-' + str(i) + '.csv', start_time)
    import_csv_damp(path + 'DAMP0101-' + str(i) + '.csv', start_time)
