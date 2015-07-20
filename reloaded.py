#!/usr/bin/env python
from flask import Flask, render_template
import os,boto
import boad

app = Flask(__name__)

@app.route('/')
def feed():
    b = boad.BOAD()
    return render_template('feed.html', eps=b.get_s3_eps(), mimetype='application/rss+xml')

if __name__ == '__main__':
    print 'start boad server'
    app.run(host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', '8080')))