import datetime as dt
import itertools
import logging
import os
import random
import time
import traceback

import boto3
import pytz
import requests

logging.basicConfig(level = logging.INFO)


feed_names = {1: '123456s',
            2: 'l',
            11: 'sir', 
            16: 'nqrw',
            21: 'bdfm',
            26: 'ace',
            31: 'g',
            36: 'j',
            51: '7'}

feed_ids = list(feed_names.keys())
api_key = os.environ['MTA_API_KEY']
client = boto3.client('s3')

for i in itertools.count():
    if i:
        delay = 1.0 + random.random()
        logging.debug(f'sleeping {delay}s...')
        time.sleep(delay)

    feed_id = feed_ids[i % len(feed_ids)]
    url = f'http://datamine.mta.info/mta_esi.php?key={api_key}&feed_id={feed_id}'
    try:
        now = dt.datetime.now(pytz.timezone('US/Eastern'))
        response = requests.get(url)
        logging.debug(f'got {url}')
    except:
        logging.warning(traceback.format_exc())
        continue
    
    monthstamp = now.strftime('%B_%Y').lower()
    datestamp = now.strftime('%Y%m%d')
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    filename = f'{monthstamp}/{datestamp}/gtfs_{feed_names[feed_id]}_{timestamp}.gtfs'
    client.put_object(Body=response.content, Bucket='zenabi-transit-archive', Key=filename)
    logging.info(f'put {filename} in s3')
