from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import constants
from app.database import db_conn
from app.login import login_required, login_admin_required, generate_hashed_password

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route("/")
@login_required
@login_admin_required
def user_management():
    # TODO: show a list of user and can click to view user profile
    return "user management"


@bp.route("/<username>", methods=('GET', 'POST'))
@login_required
def user_profile(username):
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        new_password_confirm = request.form['new_password_confirm']

        # TODO: verify the password satifsfy a specific format
        if new_password != new_password_confirm:
            flash('Please make sure the new password and confirm new password are the same')
            return redirect(request.url)
        elif new_password == old_password:
            flash('New password is the same as old password, please change')
            return redirect(request.url)

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


