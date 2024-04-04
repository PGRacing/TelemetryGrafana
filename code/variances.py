import csv
import numpy as np

path = 'C:/Users/malwi/Documents/MEGA/PGRacingTeam/000 telemetry_data/24-03-01 proto/cooling/cooling_system_temp_19_25_54.csv'

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



def calc_var_temp(file_path):
    with (open(file_path, "r") as file):
        data = csv.DictReader(file)
        temp_data = []
        for i in range(7):
            temp_data.append([])
        for row in data:
            temp_data[0].append(float(row['engine_out']))
            temp_data[1].append(float(row['engine_in']))
            temp_data[2].append(float(row['radiator_l_in']))
            temp_data[3].append(float(row['radiator_l_out']))
            temp_data[4].append(float(row['radiator_r_in']))
            temp_data[5].append(float(row['radiator_r_out']))
            temp_data[6].append(float(row['timestamp']))
                
            if len(temp_data[0]) > 2000:
                break
        var_sum = 0
        for i in range(6):
            var_sum += np.var(temp_data[i])

        timesteps_sum = 0
        for i in range(1, len(temp_data[6])):
            timesteps_sum += (temp_data[6][i] - temp_data[6][i-1])

        absolute_var = var_sum/6
        avg_timestep = timesteps_sum/len(temp_data[6])
    return absolute_var, avg_timestep

if __name__ == '__main__':
    #acc = calc_var_acc(file_path=path + 'RB-1.csv', sensor='racebox')
    #print(f'acc variance: {acc:.10f}')
    # for racebox: 0.0000053744
    #gyro = calc_var_gyro(file_path=path + 'RB-1.csv', sensor='racebox')
    #print(f'gyro variance: {gyro:.10f}')
    # for racebox: 0.0000053744
    #gps = calc_var_gps(file_path=path + 'RB-1.csv', sensor='racebox')
    #print(f'gps variance: {gps:.15f}')
    # for racebox: 0.000000000003664

    temp, timestep = calc_var_temp(path)
    print(f'temp variance: {temp:.15f}')
    print(f'avg timestep: {timestep:.15f}')