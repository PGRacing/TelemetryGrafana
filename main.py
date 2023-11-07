import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from conf_influxdb import *
from func_damp import *
from func_abs import *
from func_gps import *

#date = datetime(year=2023, month=11, day=5)
start_time = import_csv_gps('C:/Users/krzys/Desktop/telemetry/5.11.2023/GPS0101-13.csv')
#import_csv_damp('C:/Users/krzys/Desktop/telemetry/5.11.2023/DAMP0101-13.csv', '2023-11-05')
#import_csv_abs('C:/Users/krzys/Desktop/telemetry/5.11.2023/ABS0101-13.csv', '2023-11-05')