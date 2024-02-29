import serial

serial_com_port = "COM9"
serial_baudrate=57600

ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate)
while(True):
    line = ser.readline()