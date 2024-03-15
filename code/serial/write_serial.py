import csv
import os
import serial
import array
from datetime import datetime

path = "C:/Users/krzys/Desktop/telemetry/05.11-Pszczolki/file.csv"
path2 = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-09 Pszczolki/racebox/RaceBox_Track_Sessionon_09-03-2024_12-36.csv'
serial_com_port = "COM5"
serial_baudrate=57600

def float_to_bytes(value):
    float_array = array.array('f', [value])
    return float_array.tobytes()

def simulate_serial(filepath):
    ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate)
    file = open(filepath, "r")
    csv_reader = csv.DictReader(file)
    line_count = 0
    #startTime = datetime.datetime.now()
    print(f'Start sending data from file ${filepath}')

    for row in csv_reader:
        # corelate sending data with actual time since start
        # decide about sending frequency
        #timeSinceStart = datetime.datetime.now() - startTime
        GForceX = float(row['GForceX']) * 9.8 
        GForceY = float(row['GForceY']) * 9.8 
        GForceZ = float(row['GForceZ']) * 9.8
        float_bytes = float_to_bytes(GForceZ)        
        #ser.write((str(row["radiator_r_out"])+'\n').encode('utf-8'))
        ser.write(float_bytes)
        ser.write('\n'.encode('utf-8'))
        #ser.write((str(GForceY)+'\n').encode('utf-8'))
        #ser.write((str(GForceZ)+'\n').encode('utf-8'))
        #print(row)
        line_count += 1

    print('the end')

    #endTime = datetime.datetime.now()
    #print(f'Sent {line_count} rows in {endTime - startTime}')


if __name__ == "__main__":
    if os.path.exists(path2):
        simulate_serial(path2)