import re
import redis
import json
import time
import pytz
from datetime import datetime

import googlemaps
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore

from settings import GOOGLE_API_KEY, SECRET_KEY

app = Flask(__name__)
app.config.from_object(__name__)

store = RedisStore(redis.StrictRedis(host = '127.0.0.1', port = 6379, db = 0))
KVSessionExtension(store, app)


def direction_original(parsed, resp):
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

    start_location = parsed.group('start')
    time_type = parsed.group('timetype')

    extra_args = dict()

    '''
    If a time is specified, we need to first figure out what timezone the
    user is in. Google's Timezone API required a geocoded location, so we 
    need to use the Geocoding API to get that data from the provided start 
    location. Once we have the timezone, we get the current datetime in 
    that location, replace the time with the provided one, and get the
    resulting timestamp. Getting the current datetime from the starting 
    location is necessary since it could be offset a day from UTC.
    '''
    if time_type:
        desired_time = datetime.strptime(parsed.group('time'), '%I:%M%p')
    
        start_geocoded = gmaps.geocode(start_location)[0]['geometry']['location']

        start_timezone = gmaps.timezone(
            (start_geocoded['lat'], start_geocoded['lng']), 
            time.time()
        )['timeZoneId']

        local_datetime = datetime.now(
            pytz.timezone(start_timezone)
        ).replace(
            hour=desired_time.hour, 
            minute=desired_time.minute
        )
        
        utc_timestamp = int(time.mktime(
            local_datetime.astimezone(pytz.utc).timetuple()
        ))

        time_key = 'arrival_time' if time_type == 'at' else 'departure_time'
        extra_args[time_key] = utc_timestamp


    directions = gmaps.directions(
        start_location,
        parsed.group('destination'),
        mode=parsed.group('mode'),
        **extra_args
    )

    session['google_data'] = directions

    try:
        trip_data = directions[0]['legs'][0]
    except IndexError:
        resp.message('Sorry, that\'s too ambiguous')
        return str(resp)

    msg = '\n'

    for num, step in enumerate(trip_data['steps']):
        msg += u'{num}. {step}\n'.format(
            num=num+1, 
            step=step['html_instructions']
        )

    resp.message(msg)
    return str(resp)


def direction_expanded(parsed, resp):
    directions = session.get('google_data')

    if directions is None:
        resp.message('Sorry, there\'s no data to retrieve')
        return str(resp)

    trip_data =  directions[0]['legs'][0]['steps'][int(parsed.group('num'))-1]

    msg = '\n'

    for num, step in enumerate(trip_data['steps']):
        msg += u'{num}. {step}\n'.format(
            num=num+1, 
            step=step['html_instructions']
        )

    resp.message(msg)
    return str(resp)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    body = request.values.get('Body', '')
    resp = MessagingResponse()

    COMMANDS = {
        'How do I get to (?P<destination>.+) from (?P<start>.+?)( by (?P<mode>walking|transit))?( (?P<timetype>at|before) (?P<time>\d{1,2}(?:(?:am|pm)|(?::\d{1,2})(?:am|pm)?)))?\?': direction_original,
        'Expand on (?P<num>[0-9]+)': direction_expanded,
    }

    for cmd,fnc in COMMANDS.iteritems():
        parsed = re.search(cmd, body)

        if parsed:
            return fnc(parsed, resp)

    if parsed is None:
        resp.message('Sorry, I didn\'t get that')
        return str(resp)


if __name__ == "__main__":
    app.secret_key = SECRET_KEY
    app.run(debug=True)
