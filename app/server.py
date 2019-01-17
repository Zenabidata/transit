import datetime as dt
import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

import pandas as pd
import requests as r
from google.transit import gtfs_realtime_pb2

datapath = '/home/tanner/Documents/transit/'

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

class GetHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        trips = pd.read_csv(datapath + 'gtfs_schedule/trips.txt').dropna(how='all', axis=1)
        trip_ids = set(trips.trip_id)
        parsed_trips = pd.DataFrame(_parse_trip_id(trip_id) for trip_id in trip_ids)
        parsed_trips = parsed_trips.sort_values(['day_of_week','division','line','direction','start_time']).reset_index(drop=True)
        parsed_trips['start_time'] = parsed_trips.start_time.apply(lambda x: time_of_day_from_minutes(int(x)/100))
        self.trips_full = trips.set_index('trip_id').join(parsed_trips.set_index('trip_id'))
        print("here")
        BaseHTTPRequestHandler.__init__(self, *args)
    
    def do_GET(self):
        d = {
            "Fulton St": {
                "Uptown": [
                    {
                        "line": "A",
                        "name": "test2",
                        "time": 1547703200
                    }
                ],    
                "Downtown": [
                    {
                        "line": "A",
                        "name": "test1",
                        "time": 1547683200
                    }
                ]
            }
        }
        
        api_key = os.environ['MTA_API_KEY']

        if api_key:
            d['Fulton St']['Uptown'] = []
            d['Fulton St']['Downtown'] = []

            feed_id = 26
            stop_id = 'A38' # Fulton St
            gtfs_url = f'http://datamine.mta.info/mta_esi.php?key={api_key}&feed_id={feed_id}'
            response = r.get(gtfs_url)

            assert response.ok

            feed_message = gtfs_realtime_pb2.FeedMessage()
            feed_message.ParseFromString(response.content)

            for e in feed_message.entity:
                for stu in e.trip_update.stop_time_update:
                    if stop_id in stu.stop_id:
                        trip_id = e.trip_update.trip.trip_id
                        start_date = e.trip_update.trip.start_date
                        direction = trip_id.split('..')[-1]
                        direction_name = ''
                        if direction == 'N':
                            direction_name = "Uptown"
                        elif direction == 'S':
                            direction_name = "Downtown"

                        line = e.trip_update.trip.route_id
                        time = stu.arrival.time
                        
                        sched_trip_id = closest_trip_id(self.trips_full, start_date, trip_id)
                        name = self.trips_full.loc[sched_trip_id].trip_headsign
                        d['Fulton St'][direction_name].append({
                            'line': line,
                            'time': time,
                            'name': name
                        })

        self.send_response(200)
        self.send_header('content-type','application-json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()


        self.wfile.write(bytes(json.dumps(d), 'utf8'))
        return            

if __name__ == '__main__':
    server = HTTPServer(('localhost', 9876), GetHandler)
    print('Starting server on http://localhost:9876, use <Ctrl-C> to stop')
    server.serve_forever()
