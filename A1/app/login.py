import functools

from flask import Blueprint, g, redirect, render_template, request, session, url_for

from app import constants
from app.database import db_conn

bp = Blueprint('login', __name__, url_prefix='/login')


@bp.route('/', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # TODO: hash password and compare the hashed password
        cursor = db_conn.cursor()
        sql_stmt = "SELECT * FROM user WHERE username='{}' AND password='{}'".format(username, password)
        cursor.execute(sql_stmt)
        user = cursor.fetchone()

        error = None if user else "Incorrect username or password"
        if not error:
            session.clear()
            session["username"] = user[constants.USERNAME]
            return redirect(url_for("detection.detect"))
        # flash(error)

    return render_template('login/login.html')


@bp.route('/password_recovery', methods=('GET', 'POST'))
def password_recovery():
    return render_template("login/password_recovery.html")


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login.login"))


@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')
    if username is None:
        g.user = None
    else:
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username='{}'".format(username))
        user = cursor.fetchone()
        g.user = user


# decorator method that force all not signed request to jump back to login page
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login.login'))
        return view(**kwargs)

    return wrapped_view
