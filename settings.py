import os

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

APP_SECRET_KEY = os.environ['APP_SECRET_KEY']

DATABASE = {
    'USER': os.environ['MYSQL_USER'],
    'PWD': os.environ['MYSQL_PWD'],
    'NAME': os.environ['MYSQL_NAME'],
    'HOST': 'localhost'
}

