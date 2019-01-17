import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer  
from urllib import parse

class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        return_string = '{median:{}, sigma:{}}'
        parse_result = parse.urlparse(self.path)

        self.send_response(200)
        self.send_header('content-type','application-json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()

        d = {
            "Fulton St": [
                {
                    "Downtown":
                        [
                            {
                                "line": "A",
                                "name": "Far Rockaway",
                                "time": 1547683200
                            }
                        ]    
                }
            ]
        }

        self.wfile.write(bytes(json.dumps(d), 'utf8'))
        return            

if __name__ == '__main__':
    server = HTTPServer(('localhost', 9876), GetHandler)
    print('Starting server on http://localhost:9876, use <Ctrl-C> to stop')
    server.serve_forever()
