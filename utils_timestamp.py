import datetime

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
    print(gps_datetime)
    print(timedelta)
    return gps_datetime - timedelta

def start_time_add_timestamp(start_time, csv_timestamp):
    timedelta = csv_timestamp_to_timedelta(csv_timestamp)
    return start_time + timedelta

def start_time_add_millis_timestamp(start_time, csv_millis_timestamp):
    timedelta = csv_millis_timestamp_to_timedelta(csv_millis_timestamp)
    return start_time + timedelta