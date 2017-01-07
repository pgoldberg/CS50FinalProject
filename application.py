# -*- coding: utf-8 -*-
import os
import re
import httplib, sys
from urlparse import urlparse
from flask import Flask, jsonify, render_template, request, url_for, redirect, session, flash
from flask_jsglue import JSGlue
from passlib.apps import custom_app_context as pwd_context
from flask_session import Session
from tempfile import gettempdir
from flask_sslify import SSLify

# CS50 class library
from library50 import cs50
from helpers import *

import urlparse
import psycopg2
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

# configure application
app = Flask(__name__)
sslify = SSLify(app)

JSGlue(app)

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure CS50 Library to use database
db = SQL(os.environ["DATABASE_URL"])

@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    """Render map."""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not os.environ.get("API_KEY"):
            raise RuntimeError("API_KEY not set")
        
        # latitude and longitude of user
        lat = request.form.get("lat")
        lng = request.form.get("lng")
        
        # ensure location is obtained
        if lat == '' or lng == '':
            flash("Could not find your location")
            return render_template("index.html", key=os.environ.get("API_KEY"), alert="danger")
        
        # ensure marker has a type
        if request.form.get("type") == '':
            flash("Must select an object type")
            return render_template("index.html", key=os.environ.get("API_KEY"), alert="danger")
        
        # ensure marker has a description
        if request.form.get("desc") == '':
            flash("Must include description")
            return render_template("index.html", key=os.environ.get("API_KEY"), alert="danger")
        
        # create marker at user location with user's description
        else:
            db.execute("INSERT INTO markers1(type, descr, olat, olng, uid) VALUES(:type, :desc, :olat, :olng, :uid)",
                type=request.form.get("type"), desc=request.form.get("desc"), olat=lat, olng=lng, uid=session["user_id"])
        
        # redirect user to home page
        flash("Successfully submitted marker!")
        return render_template("index.html", key=os.environ.get("API_KEY"), alert="info")

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("index.html", key=os.environ.get("API_KEY"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("login.html")

        # ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            flash("Invalid username and/or password")
            return render_template("login.html")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))
    
@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Takes user to their profile."""
    user = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])
    markers = db.execute("SELECT * FROM markers1 WHERE uid=:id ORDER BY type", id=session["user_id"])
    # render profile page
    return render_template("profile.html", user=user, markers=markers, alert=request.args.get("alert"))    
    
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # forget any user_id
    session.clear()
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("register.html")
        
        # ensure username not taken
        elif db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username")):
            flash("Username already taken")
            return render_template("register.html")
        
        # ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("register.html")
        
        # ensure password check was submitted
        elif not request.form.get("passwordcheck"):
            flash("Must verify password")
            return render_template("register.html")
            
        #ensure passwords match
        elif not request.form.get("password") == request.form.get("passwordcheck"):
            flash("Passwords do not match")
            return render_template("register.html")
        
        # create new user
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", 
            username=request.form.get("username"), hash=pwd_context.encrypt(request.form.get("password")))
        
        # redirect user to home page
        return redirect(url_for("login"))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/search")
@login_required
def search():
    """Search for markers."""
    
    # ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")
    
    # type of marker to search for
    type = request.args.get('q')

    # ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")
    
    # explode southwest corner into two variables
    (sw_lat, sw_lng) = [float(s) for s in request.args.get("sw").split(",")]

    # explode northeast corner into two variables
    (ne_lat, ne_lng) = [float(s) for s in request.args.get("ne").split(",")]
    
    # find markers within view
    if (sw_lng <= ne_lng):

        # doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM markers1
            WHERE type=:type AND :sw_lat <= olat AND olat <= :ne_lat AND (:sw_lng <= olng AND olng <= :ne_lng)""",
            type=type, sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # crosses the antimeridian
        rows = db.execute("""SELECT * FROM markers1
            WHERE type=:type AND :sw_lat <= olat AND olat <= :ne_lat AND (:sw_lng <= oLng OR oLng <= :ne_lng)""",
            type=type, sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)
    
    for x in rows:
        x[u'olng'] = float(x[u'olng'])
        x[u'olat'] = float(x[u'olat'])
    
    return jsonify(rows)

@app.route("/vote")
@login_required
def vote():
    """Upvote or downvote marker"""
    
    # user's id
    uid = session["user_id"]
    # marker's id
    id = request.args.get("id")
    # upvote or downvote
    vote = request.args.get("vote")
    # finds user's previous vote on marker
    votes = db.execute("SELECT type FROM votes WHERE marker_id=:id AND user_id=:uid", id=id, uid=uid)
    # id of user who submitted marker
    sId = db.execute("SELECT uid FROM markers1 WHERE id=:id", id=id)
    
    # user has never voted on marker before
    if len(votes) == 0:
        if vote == "upvote":
            
            # update marker's votes, user's points
            db.execute("UPDATE markers1 SET checks=checks+1 WHERE id=:id", id=id)
            db.execute("UPDATE users SET points=points+1 WHERE id=:id", id=sId[0]["uid"])
            db.execute("INSERT INTO votes (user_id, marker_id, type) VALUES(:uid, :id, :vote)", uid=uid, id=id, vote=vote)
        
        else:
            
            # update marker's votes, user's points
            db.execute("UPDATE markers1 SET checks=checks-1 WHERE id=:id", id=id)
            db.execute("UPDATE users SET points=points-1 WHERE id=:id", id=sId[0]["uid"])
            db.execute("INSERT INTO votes (user_id, marker_id, type) VALUES(:uid, :id, :vote)", uid=uid, id=id, vote=vote)
    
    # user has voted on marker before
    else:
        # user wants to change vote
        if vote != votes[0]["type"]:
            
            # delete old vote
            db.execute("DELETE FROM votes WHERE marker_id=:id AND user_id=:uid", id=id, uid=uid)
            if vote == "upvote":
                
                # update marker's votes, user's points
                db.execute("UPDATE markers1 SET checks=checks+1 WHERE id=:id", id=id)
                db.execute("UPDATE users SET points=points+1 WHERE id=:id", id=sId[0]["uid"])
            
            else:
                
                # update marker's votes, user's points
                db.execute("UPDATE markers1 SET checks=checks-1 WHERE id=:id", id=id)
                db.execute("UPDATE users SET points=points-1 WHERE id=:id", id=sId[0]["uid"])
    
    rows = db.execute("SELECT * FROM markers1 WHERE id=:id", id=id);
    return jsonify(rows)
    
@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change password"""
    # store id of logged in user
    user_id = session["user_id"]
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure proper usage
        if not request.form.get("cur_password"):
            flash("Must enter current password")
            return render_template("password.html", alert="danger")
        if not request.form.get("new_password"):
            flash("Must enter new password")
            return render_template("password.html", alert="danger")
        if request.form.get("new_password") != request.form.get("confirm_password"):
            flash("Passwords do not match")
            return render_template("password.html", alert="danger")
        
        # get user info
        user = db.execute("SELECT hash FROM users WHERE id=:user_id", user_id=user_id)
        
        # verify correct current password
        if not pwd_context.verify(request.form.get("cur_password"), user[0]["hash"]):
            flash("Incorrect current password")
            return render_template("password.html", alert="danger")
        
        # update to new password
        db.execute("UPDATE users SET hash=:hash WHERE id=:user_id",
        hash=pwd_context.encrypt(request.form.get("new_password")), user_id=user_id)
        
        # redirect to account page and flash success message
        flash("Password successfully changed!")
        return render_template("password.html", alert="info")
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        # render the password.html template
        return render_template("password.html")
        
@app.route("/profile/remove", methods=["POST"])
@login_required
def remove():
    """Remove Marker"""
    # get marker id
    marker_id = request.form.get("marker_id")
    
    # remove marker
    db.execute("DELETE FROM markers1 WHERE id=:id AND uid=:uid", id=marker_id, uid=session["user_id"])

    rows = db.execute("SELECT * FROM markers1 WHERE id=:id AND uid=:uid", id=marker_id, uid=session["user_id"])
    if len(rows) == 0:
        flash("Successfully removed marker")
        return redirect(url_for("profile", alert="info"))
    else:
        # flash error on fail
        flash("Could not remove marker")
        return redirect(url_for("profile", alert="danger"))

if __name__ == "__main__":
    app.debug = False
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)