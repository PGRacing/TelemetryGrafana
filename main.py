from influxdb_client import InfluxDBClient, Point, WritePrecision
from conf_influxdb import *
from func_damp import *

import_csv_damp('C:/Users/krzys/Desktop/telemetry/readings/DAMP0101-22.csv', '2023-11-04')