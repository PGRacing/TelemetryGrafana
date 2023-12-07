import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = "lBvDJzs-1cHSKwdqorD4_-xxs2yeg6CgvJcPkZNADNEibLh4xLFEhjZHUIzawXhTA52Xs0MuAPZ1944IMm7Lyw=="
org = "PGRacingTeam"
url = "http://34.118.114.249/"
bucket="telemetry"

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = write_client.write_api(write_options=SYNCHRONOUS)