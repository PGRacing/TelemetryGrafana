import serial
from data_filtration import *
from lap_timer import *

serial_com_port = "COM9"
serial_baudrate=57600

gps_kalman = GPSKalman()
acc_kalman = ACCKalman()
gyro_kalman = GYROKalman()
lap_timer = LapTimer()

ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate)
while(True):
    # inity
    line = ser.readline()
    # DECODE
    # match pliku
    # funkcje
    # wysłac na influxdb po jednym
    # nowe poprzednie wartosci

