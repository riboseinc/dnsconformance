#!/usr/bin/env python3
import os.path, sys
from bottle import request, route, get, post, run, hook, app, template, view, static_file, redirect, Request
from conformdb import Conformdb
from itertools import compress,chain,cycle
from html import escape

'''
Script to allow for letting people fork the database into additional clones within the database.
This was used during the pre-release of the test suite, and is only left here in case someone
wants to spelunk how we did things.
'''

Request.MEMFILE_MAX = 1024*1024 # allow large requests

@hook('before_request')
def setup_request():
    user = request.environ.get('REMOTE_USER')
    if not user:
        user = "demo"
    request.user = user
    request.db = Conformdb(user=user)
    userinfo = request.db.getuserinfo()
    if not userinfo[0]:
        print("Bogus userinfo",userinfo[1])
        return
    request.userinfo = userinfo[1]['userwho']
    request.userpriv = userinfo[1]['userpriv'] or ""
    
def boilerplate():
    bo = "<p align=right>Logged in as {} ({})".format(request.user, request.userinfo)
    if 'Edit' in request.userpriv:
        bo += " [Can edit]"
    bo += "</p>"
    return bo


# start here
@get("/")
@view("clienthome")
def startup():
    """ return n empty status page
    """
    return dict(name="Database management", boilerplate=boilerplate())

@post("/snap")
@view("clientdone")
def snap():
    if "l" in request.forms:
        (ok, val) = request.db.clone(active=False)
    if "c" in request.forms:
        (ok, val) = request.db.clone(active=True)
    if "r" in request.forms:
        (ok, val) = request.db.clone(active=True, snapshot=True)
    if not ok:
        return failpage(val)
    return dict(res=val, name="Database management", boilerplate=boilerplate(), hostname=request.urlparts.hostname)

@view('failpage')
def failpage(why):
    """ return a failure page
    """
    return dict(boilerplate=boilerplate(), kvetch=why)

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root='./static')

# special cases
@route('/favicon.ico')
def favicon():
    return static_file("favicon.ico", root='./static')


if __name__=="__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "debug":
        # please do not change this, it's how my VM is set up
        run(host='10.0.2.15', port=8800, debug=True)
    else:
        run(server="cgi", debug=True)
