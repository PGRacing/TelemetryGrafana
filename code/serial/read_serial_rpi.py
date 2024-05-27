import serial
import struct

serial_com_port = "/dev/ttyS0"
serial_baudrate=57600

ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate)
while(True):
    line = ser.readline()
    value = struct.unpack('f', line[:-1])
    print(value)
