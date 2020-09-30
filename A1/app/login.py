import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app import constants
from app.database import db_conn

bp = Blueprint('login', __name__, url_prefix='/login')


@bp.route('/', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = authenticate(username, password)
        if not error:
            return redirect(url_for("detection.detect"))
        else:
            flash(error)
            return redirect(request.url)

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
    # TODO: this may not be needed, since we can only use session.get('username')
    #       to check in the login_required, avoid unnecessary SQL queries
    #       https://stackoverflow.com/questions/32909851/flask-session-vs-g#:~:text=session%20gives%20you%20a%20place,base%20within%20one%20request%20cycle.
    #       will need more investigation, but this is workable
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


# decorator method that force all not signed request to jump back to login page
def login_admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user[constants.ROLE] == constants.USER:
            flash("You don't have permission to access user management page")
            return redirect(url_for('detection.detect'))
        return view(**kwargs)

    return wrapped_view


def authenticate(username, password):
    # TODO: hash password and compare the hashed password
    try:
        cursor = db_conn.cursor()
        sql_stmt = "SELECT * FROM user WHERE username='{}' AND password='{}'".format(username, password)
        cursor.execute(sql_stmt)
        user = cursor.fetchone()
    except Exception as e:
        error = "Unexpected error {}".format(e)
    else:
        error = None if user else "Incorrect username or password"
        if not error and user:
            session.clear()
            session["username"] = user[constants.USERNAME]
            # load logged in user for api case, normally this will be loaded before every request
            load_logged_in_user()
    return error
