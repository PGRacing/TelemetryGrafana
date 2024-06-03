import serial
import struct
import time
import datetime
from multiprocessing import Process, Pipe, connection

serial_com_port = "COM5"
serial_baudrate=57600

ser = serial.Serial(port=serial_com_port, baudrate=serial_baudrate, inter_byte_timeout=0.001)

def receive_data():
    counter = 0
    while(True):
        line = ser.read(1024)
        if(len(line)>8 and line[0] == 0x05):
            counter+=1
            if counter == 10:
                ''' 
                arbitration id is 1 byte
                timestamp is 6 bytes (array fullfilled with 0s to 8 bytes)
                data is 2 bytes
                '''

                # id
                id = line[0] 
               # pipe.send(id)

                # timestamp
                timestamp_bytes = bytearray(line[1:7])
                for i in range(2):
                    timestamp_bytes.extend(b'\x00')
                timestamp = struct.unpack('<q', timestamp_bytes)[0]
              #  pipe.send(timestamp)
                date = datetime.datetime.fromtimestamp(timestamp/1000.0)
                print(time.time())

                # data to process later
                data = struct.unpack('>H', line[7:9])[0]
               # pipe.send(data) # TODO: send data as a list of bytes 

                print(f'id: {id}    timestamp: {date}  real timestamp:{datetime.datetime.fromtimestamp(time.time())}   data:{data}')
                print(f'delta: {datetime.datetime.fromtimestamp(time.time()) - date}')
                counter = 0

def process_data(pipe):
    arbitration_id = pipe.recv()
    timestamp = pipe.recv()
    data = pipe.recv()

    # TODO: ids still need to be defined
    # TODO: adjust functions (it was a brute force copy paste from main2 for now)

    match arbitration_id:
        # wheel speed sensor (abs) front
        case 503:
            pass

        # damper front 
        case 504:
            pass

        # gyro front
        case 507:
            pass

        # acc front
        case 508:
            pass

        # gps
        case 509:
            pass

        # wheel speed sensor (abs) rear
        case 603:
            pass

        # damper rear
        case 604:
            pass

        # gyro back
        case 607:
            pass

        # acc back
        case 608:
            pass

        # flow
        case 609:
            flow = flow_data(msg.data, timestamp, points)

        case 600:
            theoretical_heat_prev = engine_data1(msg.data, timestamp, theoretical_heat_prev, points)
        case 602:
            clt = engine_data2(msg.data, timestamp, points)
        case 606:
            engine_data6(msg.data, timestamp, points)

   # while pipe.recv() != 0xFF:
    #     pass


if __name__ == "__main__":
   # process, receive = Pipe()
   # receive = Process(target=receive_data, args=(receive,))
   # process = Process(target=process_data, args=(process,))
   # receive.start()
   # process.start()
   # receive.join()
   # process.join()
    receive_data()

    

