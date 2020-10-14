import binascii
import hashlib
import os

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app import constants
from app.database import get_conn
from app.precheck import already_login

bp = Blueprint("login", __name__, url_prefix="/login")

'''
authentication related logic file
'''


# login logic implementation
@bp.route("/", methods=("GET", "POST"))
@already_login
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Please provide both username and password when login", constants.ERROR)
            return redirect(request.url)

        error = authenticate(username, password)
        if not error:
            if not g.user[constants.MODIFIED_ANSWER]:
                flash("Please please set up your custom security answer ",constants.ERROR)
            flash("Successfully logged in", constants.INFO)
            return redirect(url_for("detection.detect"))
        else:
            flash(error, constants.ERROR)
            return redirect(request.url)

    return render_template("login/login.html")


# password recovery logic implementation
@bp.route("/password_recovery", methods=("GET", "POST"))
def password_recovery():
    if request.method == "POST":
        username = request.form.get("username")
        security_answer = request.form.get("securityanswer")
        password = request.form.get("password")
        if not username or not password or not security_answer:
            flash("Please provide all the required fields to recover your passwords", constants.ERROR)
            return redirect(request.url)

        # make queries to the SQL DB to modify the user record
        try:
            db_conn = get_conn()
            cursor = db_conn.cursor()
            sql_stmt = "SELECT * FROM user WHERE username='{}'".format(username)
            cursor.execute(sql_stmt)
            user = cursor.fetchone()
            if not user:
                db_conn.commit()
                flash("No user with username {} exists".format(username), constants.ERROR)
                return redirect(request.url)

            # verify the answer if not default
            if user[constants.MODIFIED_ANSWER] != 0:
                if verify_password(user[constants.SECURITY_ANSWER], security_answer):
                    db_conn.commit()
                    flash("Incorrect security answer", constants.ERROR)
                    return redirect(request.url)

            # change password to one provided
            new_pwd = encrypt_credentials(password)
            sql_stmt = "UPDATE user SET password='{}' WHERE username='{}'".format(new_pwd, username)
            cursor.execute(sql_stmt)
            db_conn.commit()

        except Exception as e:
            flash("Unexpected error {}".format(e), constants.ERROR)
            return redirect(request.url)
        else:
            flash("Password is reset successfully", constants.INFO)
            return redirect(url_for("login.login"))

    return render_template("login/password_recovery.html")


# logout and clear session
@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login.login"))


# make sure the user credentials are available
@bp.before_app_request
def load_logged_in_user():
    # for the image request, we just skip the user info retrieval to avoid overloading DB
    if request.path.startswith("/static"):
        return

    # for normal request, we need to ensure that we have proper user credentials
    # store username only as we want to hide user credentials from client
    username = session.get("username")
    if username is None:
        g.user = None
    else:
        db_conn = get_conn()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username='{}'".format(username))
        user = cursor.fetchone()
        g.user = user
        db_conn.commit()


# authenticate user for the login information
def authenticate(username, password):
    try:
        db_conn = get_conn()
        cursor = db_conn.cursor()
        # hash_pwd = generate_hashed_password(password)
        sql_stmt = "SELECT * FROM user WHERE username='{}'".format(username)
        cursor.execute(sql_stmt)
        user = cursor.fetchone()
        db_conn.commit()
    except Exception as e:
        error = "Unexpected error {}".format(e)
    else:
        if user:
            verified = verify_password(user[constants.PASSWORD], password)
            error = None if verified else "Incorrect username or password"
            if not error and verified:
                session.clear()
                session["username"] = user[constants.USERNAME]
                # load logged in user for api case, normally this will be loaded before every request
                load_logged_in_user()
        else:
            error = "User doesn't exist"
    return error


# Hash a credential for storing
def encrypt_credentials(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


# Verify a stored password against one provided by user
def verify_password(stored_password, provided_password):
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password
