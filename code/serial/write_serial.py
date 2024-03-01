import csv
import os
import serial
from datetime import datetime

path = "C:/Users/krzys/Desktop/telemetry/05.11-Pszczolki/file.csv"
serial_com_port = "COM9"
serial_baudrate=57600

def simulate_serial(filepath):
    ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate)
    file = open(filepath, "r")
    csv_reader = csv.DictReader(file)
    line_count = 0
    startTime = datetime.datetime.now()
    print(f'Start sending data from file ${filepath}')

    for row in csv_reader:
        # corelate sending data with actual time since start
        # decide about sending frequency
        timeSinceStart = datetime.datetime.now() - startTime
        ser.write('${row}\n'.encode('utf-8'))
        line_count += 1

    endTime = datetime.datetime.now()
    print(f'Sent {line_count} rows in {endTime - startTime}')


if __name__ == "__main__":
    if os.path.exists(path):
        simulate_serial(path)