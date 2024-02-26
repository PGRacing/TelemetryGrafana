import datetime


COEFFICIENT = 0.9473

# csv timestamp like '00:00:08:214'
# gps timestamp like '081149.88'
# gps date like '051123'

def add_start_timestamp(start_timestamp, org_timestamp):
    # add 
    # start_timestamp like: 081149.88
    # org_timestamp like: 00:00:08:214
    return

def csv_millis_timestamp_to_standard_string(date, org_timestamp):
   return str(date + 'T0{t}'.format(t=datetime.timedelta(milliseconds=int(org_timestamp))) + 'Z')

def csv_timestamp_to_standard_string(date, org_timestamp):
    return str(date + 'T' + org_timestamp[:8] + '.' + org_timestamp[9:12] + '000Z')

def csv_timestamp_to_datetime(date, csv_timestamp):
    hour = int(csv_timestamp[:2])
    minute = int(csv_timestamp[3:5])
    second = int(csv_timestamp[6:8])
    micros = int(csv_timestamp[9:]) * 1000
    return datetime.datetime(year=date.year, month=date.month, day=date.day, hour=hour, minute=minute, second=second, microsecond=micros)

def csv_millis_timestamp_to_timedelta(csv_millis_timestamp):
    return datetime.timedelta(milliseconds=int(csv_millis_timestamp))

def csv_timestamp_to_timedelta(csv_timestamp):
    hour = int(csv_timestamp[:2])
    minute = int(csv_timestamp[3:5])
    second = int(csv_timestamp[6:8])
    millis = int(csv_timestamp[9:])
    return datetime.timedelta(hours=hour, minutes=minute, seconds=second, milliseconds=millis)

def gps_utc_to_timedelta(time):
    hour = int(time[:2])
    minute = int(time[2:4])
    second = int(time[4:6])
    millis = int(time[7:])
    return datetime.timedelta(hours=hour, minutes=minute, seconds=second, milliseconds=millis)

def gps_timestamp_sub_timestamp(csv_date, gps_timestamp, csv_timestamp):
    day = int(csv_date[:2])
    month = int(csv_date[2:4])
    year = 2000 + int(csv_date[4:])
    hour = int(gps_timestamp[:2])
    minute = int(gps_timestamp[2:4])
    second = int(gps_timestamp[4:6])
    micros = int(gps_timestamp[7:])
    gps_datetime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=micros)
    timedelta = csv_timestamp_to_timedelta(csv_timestamp)
    delta = timedelta.total_seconds() * 0.9496
    dtdelta = datetime.timedelta(seconds=delta)
    return gps_datetime - dtdelta

def cooling_system_timestamp(timestamp):
    year = int(timestamp[:4])
    month = int(timestamp[5:7])
    day = int(timestamp[8:10])
    hour = int(timestamp[11:13])
    minute = int(timestamp[14:16])
    second = int(timestamp[17:19])
    milis = int(timestamp[20:])
    time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=milis)

    return time


def start_time_add_timestamp(start_time, csv_timestamp):
    timedelta = csv_timestamp_to_timedelta(csv_timestamp)
    return start_time + timedelta

def start_time_add_millis_timestamp(start_time, csv_millis_timestamp):
    timedelta = csv_millis_timestamp_to_timedelta(csv_millis_timestamp)
    return start_time + timedelta

def correct_csv_timestamp(previous_csv_timestamp, current_csv_timestamp, previous_timestamp, coefficient):
    # STRINGS: previous_csv_timestamp, current_csv_timestamp
    # DATETIME: previous_timestamp
    prev_timedelta = csv_timestamp_to_timedelta(previous_csv_timestamp)
    curr_timedelta = csv_timestamp_to_timedelta(current_csv_timestamp)
    timestamp_delta_csv = curr_timedelta - prev_timedelta
    total_seconds = timestamp_delta_csv.total_seconds()
    total_seconds *= coefficient
    timedelta = datetime.timedelta(seconds=total_seconds)
    return previous_timestamp + timedelta


def correct_csv_timestamp_millis(previous_csv_timestamp, current_csv_timestamp, previous_timestamp, time_coefficient):
    # STRING: previous_csv_timestamp
    # DATETIME: previous_timestamp, current_csv_timestamp
    previous_csv_timestamp = csv_millis_timestamp_to_timedelta(previous_csv_timestamp)
    timestamp_delta_csv = current_csv_timestamp - previous_csv_timestamp
    total_seconds = timestamp_delta_csv.total_seconds()
    #print(total_seconds)
    #print(type(total_seconds))
    #print(time_coefficient)
    #print(type(time_coefficient))
    total_seconds *= time_coefficient
    delta = datetime.timedelta(seconds=total_seconds)
    return previous_timestamp + delta

def correct_init_time(init_time):
    seconds = init_time.total_seconds() * 0.9496
    corrected_start_time = datetime.timedelta(seconds=seconds)
    return corrected_start_time

def correct_init_time_millis(init_time):
    init_time *= 0.9496
    corrected_start_time = datetime.timedelta(milliseconds=init_time)
    return corrected_start_time

def correct_gp_start_time(time):
    time2 = csv_timestamp_to_timedelta(time)
    start_time = correct_init_time(time2)
    return start_time

def set_new_coefficient(previous_utc, current_utc, previous_timestamp, current_timestamp):
    prev_timedelta = csv_timestamp_to_timedelta(previous_timestamp)
    curr_timedelta = csv_timestamp_to_timedelta(current_timestamp)
    timestamp_delta_csv = curr_timedelta - prev_timedelta
    total_seconds = timestamp_delta_csv.total_seconds()
    utc_delta = (gps_utc_to_timedelta(current_utc) - gps_utc_to_timedelta(previous_utc)).total_seconds()
    coefficient = utc_delta/total_seconds
    if coefficient == 0.:
        coefficient = 0.9496
    return coefficient

GPS = [
    [1, 0.95],
    [2, 0.9430462149033412],
    [3, 0.9406291849728637],
    [4, 0.9416745061147694],
    [5, 0.95],
    [6, 0.9404960620665335],
    [7, 0.9360110349987141],
    [8, 0.95],
    [9, 0.9426679548507199],
    [10, 0.95],
    [11, 0.95],
    [12, 0.9473],
    [13, 0.946],
    [14, 0.95], # short 
    [15, 0.95], # short
    [16, 0.95], # short
    [17, 0.9618],
    [18, 0.9588614800759013],
    [19, 0.9577150505792329],
    [20, 0.95],
    [21, 0.95],
    [22, 0.956392240359593],
    [23, 0.9574681445691818],
    [24, 0.95],
    [25, 0.95],
    [26, 0.95],
    [27, 0.9548502453607084],
    [28, 0.95],
    [29, 0.95],
    [30, 0.95],
    [31, 0.9529752568545199],
    [32, 0.95],]