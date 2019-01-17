import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer  
from urllib import parse
import requests as r
from google.transit import gtfs_realtime_pb2

class GetHandler(BaseHTTPRequestHandler):
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
                        direction = trip_id.split('..')[-1]
                        direction_name = ''
                        if direction == 'N':
                            direction_name = "Uptown"
                        elif direction == 'S':
                            direction_name = "Downtown"

                        line = e.trip_update.trip.route_id
                        time = stu.arrival.time
                        name = "Annandale" #TODO
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
