import re
import redis
import json
from flask import Flask, request, session
from flask_kvsession import KVSessionExtension
from datetime import datetime
from simplekv.memory.redisstore import RedisStore

import googlemaps
from twilio.twiml.messaging_response import MessagingResponse

from settings import GOOGLE_API_KEY, SECRET_KEY

app = Flask(__name__)
app.config.from_object(__name__)

store = RedisStore(redis.StrictRedis(host = '127.0.0.1', port = 6379, db = 0))
KVSessionExtension(store, app)

direction_re = 'How do I get to (?P<destination>.+) from (?P<start>.+) by (?P<mode>walking|transit)?\?'

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    body = request.values.get('Body')
    resp = MessagingResponse()

    parsed = re.search(direction_re, body)

    if parsed is None:
        resp.message('Sorry, I didn\'t get that')
        return str(resp)

    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

    directions = gmaps.directions(
        parsed.group('start'),
        parsed.group('destination'),
        mode=parsed.group('mode'),
        departure_time=datetime.now()
    )

    session['google_data'] = directions

    try:
        trip_data = directions[0]['legs'][0]
    except IndexError:
        resp.message('Sorry, that\'s too ambiguous')
        return str(resp)

    msg = '\n'

    for num, step in enumerate(trip_data['steps']):
        msg += '{num}. {step}\n'.format(
            num=num+1, 
            step=step['html_instructions']
        )

    resp.message(msg)
    return str(resp)

if __name__ == "__main__":
    app.secret_key = SECRET_KEY
    app.run(debug=True)
