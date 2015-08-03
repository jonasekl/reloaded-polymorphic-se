#!/usr/bin/env python
from flask import Flask, render_template, request, Response
from functools import wraps
import os,boto
import boad
import atexit
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
cron = BackgroundScheduler()
cron.start()

@cron.interval_schedule(hours=1)
def job_function():
    # Do your work here
    print 'get latest reloaded eps'

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == os.environ.get('BOAD_USERNAME') and password == os.environ.get('BOAD_PASSWORD')

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Get an account on www.bigoanddukes.com.\n'
    'Do NOT be a taker!', 401,
    {'WWW-Authenticate': 'Basic realm="Get and account on bigoanddukes.com. Dont be a taker!"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth
def feed():
    b = boad.BOAD()
    return render_template('feed.html', eps=b.get_s3_eps(), mimetype='application/rss+xml')


# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))

if __name__ == '__main__':
    print 'start boad server'
    app.run(host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', '8080')))
    
    
    
    
    
    
    