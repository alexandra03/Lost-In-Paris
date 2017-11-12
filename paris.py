import re
import redis
import json
import time
import pytz
import os
from datetime import datetime

import googlemaps
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session, g, current_app
from flaskext.mysql import MySQL
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore

import settings

app = Flask(__name__)
app.config.from_object(__name__)
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = settings.DATABASE['USER']
app.config['MYSQL_DATABASE_PASSWORD'] = settings.DATABASE['PWD']
app.config['MYSQL_DATABASE_DB'] = settings.DATABASE['NAME']
app.config['MYSQL_DATABASE_HOST'] = settings.DATABASE['HOST']

mysql.init_app(app)

app.secret_key = settings.APP_SECRET_KEY

store = RedisStore(redis.StrictRedis(host = '127.0.0.1', port = 6379, db = 0))
KVSessionExtension(store, app)

def get_db():
    if not hasattr(g, 'mysql_db'):
        g.mysql_db = mysql.connect()
    return g.mysql_db

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().execute(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

def direction_original(parsed, resp, fromNumber):
    gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)

    start_location = parsed.group('start')
    time_type = parsed.group('timetype')
    time_string = parsed.group('time')

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
        try:
            desired_time = datetime.strptime(time_string, '%I:%M%p')
        except ValueError:
            desired_time = datetime.strptime(time_string, '%I%p')

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

    '''
    Check and see whether the destination is a saved alias
    for the current phone number
    '''
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT location.address FROM location\
        JOIN phone on location.phone_id=phone.id\
        WHERE phone.number=%s AND location.alias=%s", 
        [fromNumber, parsed.group('destination').lower()]
    )

    entry = cur.fetchone()

    destination = entry[0] if entry else parsed.group('destination')

    directions = gmaps.directions(
        start_location,
        destination,
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


def direction_expanded(parsed, resp, fromNumber):
    directions = session.get('google_data')

    if directions is None:
        resp.message('Sorry, there\'s no data to retrieve')
        return str(resp)

    trip_data =  directions[0]['legs'][0]['steps'][int(parsed.group('num'))-1]

    msg = '\n'

    if 'steps' in trip_data:
        for num, step in enumerate(trip_data['steps']):
            msg += u'{num}. {step}\n'.format(
                num=num+1, 
                step=step['html_instructions']
            )
    elif 'transit_details' in trip_data:
        msg += '%(dist)s, %(dur)s, Name: %(name)s' % {
           'dist':  trip_data['distance']['text'],
            'dur': trip_data['duration']['text'],
            'name': trip_data['transit_details']['line']['short_name']
        }

    resp.message(msg)
    return str(resp)


def save_alias(parsed, resp, fromNumber):
    db = get_db()

    db.cursor().execute(
        "INSERT INTO location (address, alias, phone_id) VALUES (%s, %s, (SELECT id from phone WHERE number=%s));",
        [parsed.group('address'), parsed.group('alias').lower(), fromNumber]
    )
    db.commit()
    resp.message('Your address alias "%s" has been saved.' % parsed.group('alias'))
    return str(resp)

@app.route("/", methods=['GET', 'POST'])
def home():
    return "Hello world!"

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    body = request.values.get('Body', '')
    fromNumber = request.values.get('From')
    resp = MessagingResponse()

    db = get_db()
    db.cursor().execute('INSERT IGNORE INTO phone (number) VALUES (%s)', (fromNumber,))
    db.commit()

    COMMANDS = {
        'How do I get to (?P<destination>.+) from (?P<start>.+?)( by (?P<mode>walking|transit))?( (?P<timetype>at|before) (?P<time>\d{1,2}(?:(?:am|pm)|(?::\d{1,2})(?:am|pm)?)))?\?': direction_original,
        'Expand on (?P<num>[0-9]+)': direction_expanded,
        'Save (?P<address>.*)(?=( as )) as (?P<alias>.*)': save_alias,
    }

    for cmd,fnc in COMMANDS.iteritems():
        parsed = re.search(cmd, body)

        if parsed:
            return fnc(parsed, resp, fromNumber)

    if parsed is None:
        resp.message('Sorry, I didn\'t get that')
        return str(resp)


if __name__ == "__main__":
    app.run(debug=True)
