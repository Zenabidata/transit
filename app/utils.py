import pandas as pd
import re
import datetime as dt
from google.transit import gtfs_realtime_pb2
#from python_src import nyct_subway_pb2


datapath = '/home/tanner/Documents/transit/'

vehicle_stop_statuses  = {v.number: v.name for v in gtfs_realtime_pb2._VEHICLEPOSITION_VEHICLESTOPSTATUS.values}
#directions             = {v.number: v.name for v in nyct_subway_pb2._NYCTTRIPDESCRIPTOR_DIRECTION.values}
schedule_relationships = {v.number: v.name for v in gtfs_realtime_pb2._TRIPDESCRIPTOR_SCHEDULERELATIONSHIP.values}

def time_of_day_from_unix_ts(ts):
  """unix timestamp to time of day"""
  return dt.datetime.fromtimestamp(ts).time()

def time_of_day_from_minutes(mins):
  """minutes after midnight to standard time of day"""
  return (dt.datetime(1,1,1) + dt.timedelta(minutes = mins)).time()

def day_of_week_from_datestamp(datestamp):
  """Datestamps like '20180902' -> 6 (for Sunday)"""
  if not(len(datestamp) == 8 and datestamp.isdigit()):
    raise ValueError(f"invalid datestamp: {datestamp}")
  year = int(datestamp[:4])
  month = int(datestamp[4:6])
  day = int(datestamp[6:])
  return dt.date(year, month, day).weekday()

day1 = dt.date(1,1,1)
day2 = dt.date(1,1,2)

def timediff(time1, time2):
  """finds the minimum time between two time-of-day-stamps"""
  if time1 > time2:
    time1, time2 = time2, time1
  diff1 = dt.datetime.combine(day1, time2) - dt.datetime.combine(day1, time1)
  diff2 = dt.datetime.combine(day2, time1) - dt.datetime.combine(day1, time2)
  return min(diff1, diff2)


trip_id_re = re.compile(r'(A|B|(SIR-))((SP)|(FA))(20)?\d{2}(GEN)?-([0-9A-Z]\w?)\d{3}-(\w+)-\d{2}_(\d+)_([0-9A-Z]\w?)\.\.?([NS])(\d{2}(R|X)(\d{3})?)')

def _parse_trip_id(trip_id):
  m = re.match(trip_id_re, trip_id)
  if m is None:
    raise ValueError(f'no match: {trip_id}')
  groups = m.groups()
  if groups[7] != groups[10]:
    raise ValueError(f"incongruent id: {trip_id}")
  return {'trip_id': trip_id,
          'division': groups[0],
          'line': groups[7],
          'day_of_week': groups[8],
          'start_time': groups[9],
          'direction': groups[11],
          'trip_path': groups[12]}

def get_gtfs_sched():
  agency = pd.read_csv(datapath + 'gtfs_schedule/agency.txt')
  
  routes = pd.read_csv(datapath + 'gtfs_schedule/routes.txt')
  
  trips = pd.read_csv(datapath + 'gtfs_schedule/trips.txt').dropna(how='all', axis=1)
  trip_ids = set(trips.trip_id)
  parsed_trips = pd.DataFrame(_parse_trip_id(trip_id) for trip_id in trip_ids)
  parsed_trips = parsed_trips.sort_values(['day_of_week','division','line','direction','start_time']).reset_index(drop=True)
  parsed_trips['start_time'] = parsed_trips.start_time.apply(lambda x: time_of_day_from_minutes(int(x)/100))
  trips_full = trips.set_index('trip_id').join(parsed_trips.set_index('trip_id'))

  stop_times = pd.read_csv(datapath + 'gtfs_schedule/stop_times.txt').dropna(how='all', axis=1)
  stop_times['route_id'] = stop_times.trip_id.str.extract('_([^_]*)\.\.')

  stops = pd.read_csv(datapath + 'gtfs_schedule/stops.txt').dropna(how='all', axis=1)

  calendar_dates = pd.read_csv(datapath + 'gtfs_schedule/calendar_dates.txt')

  calendar = pd.read_csv(datapath + 'gtfs_schedule/calendar.txt')

  transfers = pd.read_csv(datapath + 'gtfs_schedule/transfers.txt')

  shapes = pd.read_csv(datapath + 'gtfs_schedule/shapes.txt').dropna(how='all', axis=1)

  return {'agency': agency,
          'routes': routes,
          'trips': trips_full,
          'stop_times': stop_times,
          'stops': stops,
          'calendar_dates': calendar_dates,
          'calendar': calendar,
          'transfers': transfers,
          'shapes': shapes}

_short_trip_id_re = re.compile(r'(\d{6})_(\w)..(\w)')

def _parse_short_trip_id(trip_id):
  m = re.match(_short_trip_id_re, trip_id)
  if m is None:
    raise ValueError(f'no match: {trip_id}')
  groups = m.groups()
  timestamp = groups[0]
  line = groups[1]
  direction = groups[2]
  return timestamp, line, direction

_days =  {0: 'Weekday',
          1: 'Weekday',
          2: 'Weekday',
          3: 'Weekday',
          4: 'Weekday',
          5: 'Saturday',
          6: 'Sunday'}

def closest_trip_id(trips_df, start_date, rt_trip_id):
  """finds the scheduled trip_id most similar to the given rt_trip_id
     
  :param trips_df: schedule of trips, indexed by trip_id
  :type trips_df: DataFrame
  :param start_date: date on which the trip started
  :type start_date: str (ex: '20180801')
  :param rt_trip_id: realtime trip_id
  :type rt_trip_id: str
  :rtype: str
  """

  timestamp, line, direction = _parse_short_trip_id(rt_trip_id)

  day_of_week = _days[day_of_week_from_datestamp(start_date)]
  time_of_day = time_of_day_from_minutes(int(timestamp)/100)

  relevant_trips = trips_df[(trips_df.line == line)
                          & (trips_df.direction == direction)
                          & (trips_df.day_of_week == day_of_week)]

  closest_trip_id = (relevant_trips.start_time
                     .apply(lambda ts: timediff(ts, time_of_day))
                     .idxmin())
  return closest_trip_id

  