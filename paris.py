import re
from flask import Flask, request
from datetime import datetime

import googlemaps
from twilio.twiml.messaging_response import MessagingResponse

from settings import GOOGLE_API_KEY

app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    body = request.values.get('Body')
    resp = MessagingResponse()

    try:
        destination = re.search('How do I get to (.+)\?', body).group(1)
    except AttributeError:
        resp.message('Sorry, I didn\'t get that')
        return str(resp)

    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

    directions = gmaps.directions(
        "Union Station, Toronto",
        destination,
        mode="transit",
        departure_time=datetime.now()
    )

    trip_data = directions[0]['legs'][0]

    msg = '\n'

    for num, step in enumerate(trip_data['steps']):
        msg += '{num}. {step}\n'.format(
            num=num+1, 
            step=step['html_instructions']
        )

    resp.message(msg)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
