import csv
from datetime import datetime
from conf_influxdb import *
from utils_timestamp import *
from test_functions.filters import low_pass_filter, get_alpha

low_pass_filter_alpha_4Hz = get_alpha(0.004, 4)

def import_csv_abs(filepath, start_time):
    # CSV column names as following:
    # timestamp,ID,speed
    # date like '2023-11-04'
    file = open(filepath, "r")
    csv_reader = csv.DictReader(file)
    line_count = 0
    points = []
    startTime = datetime.datetime.now()
    previous_timestamp = None
    previous_csv_timestamp = None
    prev_speed = [0.0,0.0]

    for row in csv_reader:
        #print(f'{row["timestamp"]}; {row["ID"]}; {row["speed"]}')
        # TODO switch timestamp format

        timestamp = start_time_add_millis_timestamp(start_time, row["timestamp"])

        #if line_count < 2:
            #first_timestamp_millis = correct_init_time_millis(int(row["timestamp"]))
            #timestamp = start_time + first_timestamp_millis
        #else:
            #if len(time_coefficients) == 1:
                #time_coefficient = 0.9489
            #else:
                #for i in range (1, len(time_coefficients)):
                    #if csv_millis_timestamp_to_timedelta(row["timestamp"]) >= csv_timestamp_to_timedelta(time_coefficients[i-1][0]) and \
                    #csv_millis_timestamp_to_timedelta(row["timestamp"]) < csv_timestamp_to_timedelta(time_coefficients[i][0]):
                        #time_coefficient = time_coefficients[i-1][1]
                    #elif csv_millis_timestamp_to_timedelta(row["timestamp"]) <= csv_timestamp_to_timedelta(time_coefficients[0][0]):
                        #time_coefficient = time_coefficients[0][1]
                    #elif csv_millis_timestamp_to_timedelta(row["timestamp"]) >= csv_timestamp_to_timedelta(time_coefficients[len(time_coefficients) - 1][0]):
                        #time_coefficient = time_coefficients[len(time_coefficients) - 1][1]

            #csv_timestamp = csv_millis_timestamp_to_timedelta(row["timestamp"])
            #timestamp = correct_csv_timestamp_millis(previous_csv_timestamp, csv_timestamp, previous_timestamp, time_coefficient)
        #if line_count % 2 == 1:
            #previous_timestamp = timestamp
            #previous_csv_timestamp = row["timestamp"]

        speed = low_pass_filter(float(row["speed"])*2.0, prev_speed[int(row["ID"])-4], low_pass_filter_alpha_4Hz)
        prev_speed[int(row["ID"])-4] = speed
        point = (
            Point('abs')
            .tag("ID", f'{row["ID"]}')
            .field("speed", speed)
            .time(timestamp)
        )
        points.append(point)
        if line_count % 5000 == 0:
            write_api.write(bucket=bucket, org=org, record=points)
            points.clear()
        line_count += 1

    write_api.write(bucket=bucket, org=org, record=points)
    endTime = datetime.datetime.now()
    file.close()
    print(f'ABS: Imported {line_count} rows in {endTime - startTime}')