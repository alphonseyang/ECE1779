import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app import constants
from app.database import db_conn

bp = Blueprint("login", __name__, url_prefix="/login")


# TODO: direct the main page to detection is logged in else to login page
@bp.route("/", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Please provide both username and password when login")
            return redirect(request.url)

        error = authenticate(username, password)
        if not error:
            return redirect(url_for("detection.detect"))
        else:
            # TODO: show the flash in the view
            flash(error)
            return redirect(request.url)

    return render_template("login/login.html")


@bp.route("/password_change", methods=("GET", "POST"))
def password_recovery():
    if request.method == "POST":
        username = request.form.get("username")
        security_answer = request.form.get("securityanswer")
        password = request.form.get("password")
        if not username or not password or not security_answer:
            flash("Please provide all the required fields to recover your passwords")
            return redirect(request.url)
        # make queries to the SQL DB to modify the user record
        try:
            cursor = db_conn.cursor()
            sql_stmt = "SELECT * FROM user WHERE username='{}'".format(username)
            cursor.execute(sql_stmt)
            user = cursor.fetchone()
            if not user:
                db_conn.rollback()
                flash("non existed user")
                return redirect(request.url)
            if user[4] != 0:
                ans = generate_hashed_password(security_answer)
                sql_stmt = "SELECT * FROM user WHERE username='{}' AND  security_answer='{}'".format(username, ans)
                cursor.execute(sql_stmt)
                user = cursor.fetchone()
                if not user:
                    db_conn.rollback()
                    flash("Incorrect security answer")
                    return redirect(request.url)
            new_pwd = generate_hashed_password(password)
            sql_stmt = "UPDATE user SET password='{}' WHERE username='{}'".format(new_pwd, username)
            cursor.execute(sql_stmt)
            db_conn.commit()
        except Exception as e:
            flash("Unexpected error {}".format(e))
            return redirect(request.url)
        else:
            flash("security answer is updated successfully")
            modified_default = True
            return render_template("login/login.html")
    return render_template("login/password_recovery.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login.login"))


@bp.before_app_request
def load_logged_in_user():
    username = session.get("username")
    if username is None:
        g.user = None
    else:
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username='{}'".format(username))
        user = cursor.fetchone()
        g.user = user
        db_conn.rollback()


# decorator method that force all not signed request to jump back to login page
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login.login"))
        return view(**kwargs)

    return wrapped_view


# decorator method that force all not signed request to jump back to login page
def login_admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user[constants.ROLE] == constants.USER:
            flash("You don't have permission to access user management page")
            return redirect(url_for("detection.detect"))
        return view(**kwargs)

    return wrapped_view


def authenticate(username, password):
    try:
        cursor = db_conn.cursor()
        hash_pwd = generate_hashed_password(password)
        sql_stmt = "SELECT * FROM user WHERE username='{}' AND password='{}'".format(username, hash_pwd)
        cursor.execute(sql_stmt)
        user = cursor.fetchone()
        db_conn.rollback()
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


def generate_hashed_password(password):
    # TODO: hash password
    return password
