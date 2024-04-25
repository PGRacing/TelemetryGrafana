import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = "IQDCW_1Gmuc-Qwu4tG5uYDlqyL9Pc9NgWmWQh2JdiUGfIGJL9gaHzT1GwPQxZwfF4at_5hHJC70lARcAjE6cCQ=="
org = "PGRacingTeam"
url = "http://185.237.15.60:8086/"
#bucket="telemetry-2023-11-05-Racebox"
bucket="telemetry-2023-11-05"

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = write_client.write_api(write_options=SYNCHRONOUS)