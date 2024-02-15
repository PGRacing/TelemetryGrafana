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
    delta = timedelta.total_seconds() * COEFFICIENT
    dtdelta = datetime.timedelta(seconds=delta)
    return gps_datetime - dtdelta

def start_time_add_timestamp(start_time, csv_timestamp):
    timedelta = csv_timestamp_to_timedelta(csv_timestamp)
    return start_time + timedelta

def start_time_add_millis_timestamp(start_time, csv_millis_timestamp):
    timedelta = csv_millis_timestamp_to_timedelta(csv_millis_timestamp)
    return start_time + timedelta

def correct_csv_timestamp(previous_csv_timestamp, current_csv_timestamp, previous_timestamp):
    # STRINGS: previous_csv_timestamp, current_csv_timestamp
    # DATETIME: previous_timestamp
    prev_timedelta = csv_timestamp_to_timedelta(previous_csv_timestamp)
    curr_timedelta = csv_timestamp_to_timedelta(current_csv_timestamp)
    timestamp_delta_csv = curr_timedelta - prev_timedelta
    total_seconds = timestamp_delta_csv.total_seconds()
    total_seconds *= COEFFICIENT
    timedelta = datetime.timedelta(seconds=total_seconds)
    return previous_timestamp + timedelta


def correct_csv_timestamp_millis(previous_csv_timestamp, current_csv_timestamp, previous_timestamp):
    # STRING: previous_csv_timestamp
    # DATETIME: previous_timestamp, current_csv_timestamp
    previous_csv_timestamp = csv_millis_timestamp_to_timedelta(previous_csv_timestamp)
    timestamp_delta_csv = current_csv_timestamp - previous_csv_timestamp
    total_seconds = timestamp_delta_csv.total_seconds()
    total_seconds *= COEFFICIENT
    delta = datetime.timedelta(seconds=total_seconds)
    return previous_timestamp + delta

def correct_init_time(init_time):
    seconds = init_time.total_seconds() * COEFFICIENT
    corrected_start_time = datetime.timedelta(seconds=seconds)
    return corrected_start_time

def correct_init_time_millis(init_time):
    init_time *= COEFFICIENT
    corrected_start_time = datetime.timedelta(milliseconds=init_time)
    return corrected_start_time

def correct_gp_start_time(time):
    time2 = csv_timestamp_to_timedelta(time)
    start_time = correct_init_time(time2)
    return start_time