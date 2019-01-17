import datetime as dt
import json
import os
import random
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

import pandas as pd
import requests as r
from google.transit import gtfs_realtime_pb2
from utils import (time_of_day_from_unix_ts,
                   time_of_day_from_minutes,
                   day_of_week_from_datestamp,
                   timediff,
                   get_gtfs_sched,
                   datapath,
                   vehicle_stop_statuses,
                   schedule_relationships,
                   closest_trip_id)



class GetHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        sched = get_gtfs_sched()
        self.trips_full = sched['trips']
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
                        arr_time = stu.arrival.time
                        if arr_time - time.time() > 1920 or arr_time - time.time() < 0:
                            continue

                        arr_time += 10*60*random.random()
                        trip_id = e.trip_update.trip.trip_id
                        start_date = e.trip_update.trip.start_date
                        direction = trip_id.split('..')[-1]
                        direction_name = ''
                        if direction == 'N':
                            direction_name = "Uptown"
                        elif direction == 'S':
                            direction_name = "Downtown"

                        line = e.trip_update.trip.route_id
                        
                        sched_trip_id = closest_trip_id(self.trips_full, start_date, trip_id)
                        name = self.trips_full.loc[sched_trip_id].trip_headsign
                        d['Fulton St'][direction_name].append({
                            'line': line,
                            'time': arr_time,
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
