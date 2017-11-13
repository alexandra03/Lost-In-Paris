# Lost In Paris
If you're anything like me, you need to check Google Maps for directions every 5 minutes even when you're right at home. But when you're travelling, paying $1M/day just to get access to slow data so you can look up how to get somewhere is a little excessive. Downloading part of a city for offline use on the Maps app is great, but the driving-only directions are almost useless in cities like Paris or Tokyo where you mainly get around by walking or transit. Hence the need for Lost-in-Paris! No need to download any apps onto your phone since it interacts over sms, and no need to sign up for an account -- all data is tied to your phone number. Send messages like the ones below to set up your own address book, get directions to your destination by your preferred method (walking or transit), get detailed directions where needed, and plan ahead by checking what the best way of getting somewhere will be at a given time. 


### Example messages

**Save 200 University Ave W, Waterloo, ON as school.**
> Your address alias "school" has been saved.

**How do I get to school from 1 Columbia St W, Waterloo ON?**
> 1. Head southwest on Columbia St W toward Spruce St
> 2. Turn left onto Albert St
> 3. Turn right onto University Ave W. Destination will be on the right.

**How do I get to school from 1 Columbia St W, Waterloo ON by transit?**
> 1. Walk to Hazel/Columbia
> 2. Bus toward UW
> 3. Walk to Environment 2, 200 University Ave W, Waterloo ON

**Expand on 2**
> 1.8km, 5mins, Name: 9

**How do I get to school from Charles st Terminal, Kitchener ON before 10:30pm?**
> 1. Walk to Charles st Terminal
> 2. Bus toward University/King via Franklin & Westmount
> 3. Walk to Environment 2, 200 University Ave W, Waterloo ON


### Setup
- Clone the repo
- Create a new mySQL database and set up tables with schema.sql
- Create a Google app with access to location, timezone, and directions APIs
- Set up all required env variables from settings.py (Google API key, DB info, Redis info)
- Run the following commands:
```
  pip install -r requirements.txt
  gunicorn paris
  redis-server
```
