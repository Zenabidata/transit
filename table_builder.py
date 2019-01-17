from google.transit import gtfs_realtime_pb2
from python_src import nyct_subway_pb2
import os
import re
import pandas as pd
import datetime
import time
import logging
from collections import defaultdict

from protobuf_to_dict import protobuf_to_dict
from app.utils import (time_of_day_from_unix_ts,
                   time_of_day_from_minutes,
                   day_of_week_from_datestamp,
                   timediff,
                   get_gtfs_sched,
                   datapath,
                   vehicle_stop_statuses,
                   schedule_relationships)

logging.basicConfig(level = logging.INFO)

def grouped_entities(feed_message):
  if len(feed_message.entity) %2 != 0:
    raise ValueError('odd number of entities')
  for e1, e2 in zip(feed_message.entity[::2], feed_message.entity[1::2]):
    yield e1.trip_update, e2.vehicle
  return

months = ['august',
          'september',
          'october',
          'november',
          'december']
def build_table():
  basepath = datapath + 'gtfs_realtime/'
  for month in months:
    month_path = basepath + month + '_2018/'
    for date in sorted(fname for fname in os.listdir(month_path) if '.' not in fname):
      date_path = month_path + date + '/'
      processed_schedule = defaultdict(dict)
      prev_next_stops = {}
      for filename in sorted(os.listdir(month_path+date)):
        if filename.split('_')[1] == 'ace':
          with open(date_path + filename, 'rb') as f:
            content = f.read()
          feed_message = gtfs_realtime_pb2.FeedMessage()
          try:
            feed_message.ParseFromString(content)
          except KeyboardInterrupt:
            raise
          except BaseException as e:
            logging.warning(f'skipping {filename}: {e}')

          logging.info(f'opened {filename}')
          
          for e in feed_message.entity: # only one of these will match the trip_id (in theory)
              if (e.HasField('trip_update')
                  and e.trip_update.trip.trip_id.endswith('A..S')
                  and e.trip_update.stop_time_update):
                trip_id = e.trip_update.trip.trip_id
                next_stop = min((stu.arrival.time, stu.stop_id) for stu in e.trip_update.stop_time_update)
                if trip_id not in prev_next_stops:
                  prev_next_stops[trip_id] = next_stop

                prev_next_stop = prev_next_stops[trip_id]
                if next_stop[1] != prev_next_stop[1]:
                  processed_schedule[date + '_' + trip_id][(next_stop[1], 'arrival')] = time_of_day_from_unix_ts(next_stop[0])
                  processed_schedule[date + '_' + trip_id][(prev_next_stop[1], 'departure')] = time_of_day_from_unix_ts(prev_next_stop[0])
                
                prev_next_stops[trip_id] = next_stop

      ps = ({'trip_id': trip_id, **d} for trip_id, d in processed_schedule.items())
      ps = pd.DataFrame(ps).set_index('trip_id').sort_index().sort_index(axis=1)
      ps.columns = pd.MultiIndex.from_tuples(ps.columns)
      ps.to_csv(f'{date}.csv')


if __name__ == "__main__":
  build_table()








