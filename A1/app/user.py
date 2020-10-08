from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app import constants
from app.api import register_worker
from app.database import db_conn
from app.login import login_required, login_admin_required, generate_hashed_password

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("/")
@login_required
@login_admin_required
def user_management():
    cursor = db_conn.cursor()
    sql_stmt = "SELECT username FROM user WHERE role='{}'".format(constants.USER)
    cursor.execute(sql_stmt)
    user = [i[0] for i in cursor.fetchall()]
    return render_template("user/user_management.html", users=user)


@bp.route("/<username>", methods=("GET", "POST"))
@login_required
def user_profile(username):
    # for POST method, only used for password change
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        new_password_confirm = request.form.get("new_password_confirm")
        if not old_password or not new_password or not new_password_confirm:
            flash("Please provide old password, new password and confirm new password when change password")
            return redirect(request.url)

        # TODO: verify the password satisfy a specific format
        if new_password != new_password_confirm:
            flash("Please make sure the new password and confirm new password are the same")
            return redirect(request.url)
        elif new_password == old_password:
            flash("New password is the same as old password, please change")
            return redirect(request.url)

        # make queries to the SQL DB to modify the user record
        try:
            cursor = db_conn.cursor()
            hash_pwd = generate_hashed_password(old_password)
            sql_stmt = "SELECT * FROM user WHERE username='{}' AND password='{}'".format(username, hash_pwd)
            cursor.execute(sql_stmt)
            user = cursor.fetchone()
            if not user:
                flash("Incorrect password")
                return redirect(request.url)
            new_hash_pwd = generate_hashed_password(new_password)
            sql_stmt = "UPDATE user SET password='{}' WHERE username='{}'".format(new_hash_pwd, username)
            cursor.execute(sql_stmt)
            db_conn.commit()
        except Exception as e:
            flash("Unexpected error {}".format(e))
            return redirect(request.url)
        else:
            flash("Password is updated successfully")
            return render_template("user/profile.html", username=username)

    # for GET method, user only allows to access their own profile
    else:
        if g.user[constants.USERNAME] == username:
            return render_template("user/profile.html", username=username)
        else:
            flash("Cannot access other user's profile")
            return redirect(url_for("detection.detect"))


@bp.route("/create", methods=["POST"])
@login_required
@login_admin_required
def create_user():
    response, _ = register_worker.work()
    if response["success"]:
        flash("Successfully created user")
    else:
        flash(response["error"]["message"])
    return redirect(url_for("user.user_management"))


@bp.route("/delete", methods=["POST"])
@login_required
@login_admin_required
def delete_user():
    cursor = db_conn.cursor()
    username = request.form.get("username")
    try:
        sql_stmt = "SELECT * FROM user WHERE username='{}'".format(username)
        cursor.execute(sql_stmt)
        if not cursor.fetchone():
            flash("no user exist in the database")
            return redirect(url_for("user.user_management"))
        sql_stmt = "DELETE FROM user WHERE username='{}'".format(username)
        cursor.execute(sql_stmt)
        db_conn.commit()
    except Exception as e:
        flash("Unexpected error {}".format(e))
        return redirect(url_for("user.user_management"))
    else:
        flash("Successfully deleted user with username {}".format(username))
        return redirect(url_for("user.user_management"))
