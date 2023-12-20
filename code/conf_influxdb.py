import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = "LEIPXlfTBFWQ6HAcdyky81_eWDDPMNHvSTOU7E4FSbFOaaPCgCkgGGNIq6drweTuV8uv-sJpKNcGGdu7ygok5A=="
org = "PGRacingTeam"
url = "http://185.237.15.60:8086/"
#bucket="telemetry-2023-11-05-Racebox"
bucket="telemetry-2023-11-05"

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = write_client.write_api(write_options=SYNCHRONOUS)