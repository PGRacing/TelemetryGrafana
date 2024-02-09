import csv
import numpy as np

path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/23_11_05_Pszczolki/'

def calc_var_acc(file_path, sensor):
    with (open(file_path, "r") as file):
        csvreader_object = csv.reader(file)
        for i in range (1, 13):
            next(csvreader_object)
            
        data = csv.DictReader(file)
        acc_data = []
        for i in range(3):
            acc_data.append([])
        for row in data:
            if float(row['Record']) >= 4098:
                if sensor == 'racebox':
                    acc_data[0].append(float(row['GForceX']))
                    acc_data[1].append(float(row['GForceY']))
                    acc_data[2].append(float(row['GForceX']))
                else:
                    if (float(row['acc_x'])) != 0.:
                        acc_data[0].append(float(row['acc_x']))
                        acc_data[1].append(float(row['acc_y']))
                        acc_data[2].append(float(row['acc_z']))
                if len(acc_data[0]) > 730 and \
                    len(acc_data[1]) > 730 and\
                    len(acc_data[2]) > 730:
                    break
        var_x = np.var(acc_data[0])
        var_y = np.var(acc_data[1])
        var_z = np.var(acc_data[2])

        absolute_var = (var_x + var_y + var_z)/3
    return absolute_var

def calc_var_gyro(file_path, sensor):
    with (open(file_path, "r") as file):
        csvreader_object = csv.reader(file)
        for i in range (1, 13):
            next(csvreader_object)
            
        data = csv.DictReader(file)
        gyro_data = []
        for i in range(3):
            gyro_data.append([])

        for row in data:
            if float(row['Record']) >= 4098:
                if sensor == 'racebox':
                    gyro_data[0].append(float(row['GyroX']))
                    gyro_data[1].append(float(row['GyroY']))
                    gyro_data[2].append(float(row['GyroZ']))
                else:
                    if (float(row['gyro_x'])) != 0.:
                        gyro_data[0].append(float(row['gyro_x']))
                        gyro_data[1].append(float(row['gyro_y']))
                        gyro_data[2].append(float(row['gyro_z']))

                if len(gyro_data[0]) > 730 and \
                    len(gyro_data[1]) > 730 and\
                    len(gyro_data[2]) > 730:
                    break
        var_x = np.var(gyro_data[0])
        var_y = np.var(gyro_data[1])
        var_z = np.var(gyro_data[2])

        absolute_var = (var_x + var_y + var_z)/3
    return absolute_var

def calc_var_gps(file_path, sensor):
    with (open(file_path, "r") as file):
        csvreader_object = csv.reader(file)
        for i in range (1, 13):
            next(csvreader_object)
            
        data = csv.DictReader(file)
        gps_data = []
        for i in range(2):
            gps_data.append([])
        if sensor == 'racebox':
            for row in data:
                if float(row['Record']) >= 4098:
                    gps_data[0].append(float(row['Longitude']))
                    gps_data[1].append(float(row['Latitude']))
                    #print(f'adding row {row["Record"]}')
                    if len(gps_data[0]) > 730:
                        break
        else:
            for row in data:
                if (float(row['lon'])) != '':
                    lat = (float(row["lat"]) / 100 // 1) + (float(row["lat"]) % 100.0 / 60.0)
                    lon = (float(row["lon"]) / 100 // 1) + (float(row["lon"]) % 100.0 / 60.0)

                    gps_data[0].append(lat)
                    gps_data[1].append(lon)
                if len(gps_data[0]) > 1000 and \
                    len(gps_data[1]) > 1000:
                    break
        var_x = np.var(gps_data[0])
        var_y = np.var(gps_data[1])


        absolute_var = (var_x + var_y)/2
    return absolute_var

acc = calc_var_acc(file_path=path + 'RB-1.csv', sensor='racebox')
print(f'acc variance: {acc:.10f}')
# for racebox: 0.0000053744
gyro = calc_var_gyro(file_path=path + 'RB-1.csv', sensor='racebox')
print(f'gyro variance: {gyro:.10f}')
# for racebox: 0.0000053744
gps = calc_var_gps(file_path=path + 'RB-1.csv', sensor='racebox')
print(f'gps variance: {gps:.15f}')
# for racebox: 0.000000000003664