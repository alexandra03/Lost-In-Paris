import os
import urlparse

urlparse.uses_netloc.append('mysql')

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

APP_SECRET_KEY = os.environ['APP_SECRET_KEY']


if 'DATABASE_URL' in os.environ:
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    
    DATABASE = {
        'USER': url.username,
        'PWD': url.password,
        'NAME': url.path[1:],
        'HOST': url.hostname,
    }
else:
    DATABASE = {
        'USER': os.environ['MYSQL_USER'],
        'PWD': os.environ['MYSQL_PWD'],
        'NAME': os.environ['MYSQL_NAME'],
        'HOST': os.environ['MYSQL_HOST']
    }
