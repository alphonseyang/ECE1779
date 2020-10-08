from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.database import db_conn
from app.login import login_required, login_admin_required, generate_hashed_password

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route("/")
@login_required
@login_admin_required
def user_management():
    # TODO: show a list of user and can click to view user profile
    cursor = db_conn.cursor()
    sql_stmt = "SELECT username FROM user WHERE role='user'"
    cursor.execute(sql_stmt)
    user = [i[0] for i in cursor.fetchall()]
    return render_template("user/user_management.html", users=user)


@bp.route("/<username>", methods=('GET', 'POST'))
@login_required
def user_profile(username):
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        new_password_confirm = request.form.get('new_password_confirm')
        if not old_password or not new_password or not new_password_confirm:
            flash("Please provide old password, new password and confirm new password when change password")
            return redirect(request.url)

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


@bp.route("/deleteuser", methods=['POST'])
@login_required
@login_admin_required
def delete_user():
    cursor = db_conn.cursor()
    if request.method == 'POST':
        user = request.form.get('user')
    try:
        sql_stmt = "SELECT * FROM user WHERE username='{}'".format(user)
        cursor.execute(sql_stmt)
        username = cursor.fetchone()
        if not username:
            flash("no user exist in the database")
            return redirect(url_for('user.user_management'))
    except Exception as e:
        flash("Unexpected error {}".format(e))
        return redirect(url_for('user.user_management'))
    sql_stmt = "DELETE FROM user WHERE username='{}'".format(user)
    cursor.execute(sql_stmt)
    db_conn.commit()
    return redirect(url_for('user.user_management'))