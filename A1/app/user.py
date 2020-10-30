import os
import shutil

from botocore.exceptions import ClientError
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app import constants
from app.api import register_worker
from app.aws_helper import session
from app.database import get_conn
from app.login import encrypt_credentials, verify_password
from app.precheck import login_required, login_admin_required

bp = Blueprint("user", __name__, url_prefix="/user")

'''
user management logic file
'''


# user management page method
@bp.route("/")
@login_required
@login_admin_required
def user_management():
    # show a list of user for selection to delete
    db_conn = get_conn()
    cursor = db_conn.cursor()
    sql_stmt = "SELECT username FROM user WHERE role='{}'".format(constants.USER)
    cursor.execute(sql_stmt)
    user = [i[0] for i in cursor.fetchall()]
    db_conn.commit()
    return render_template("user/user_management.html", users=user)


# display user detail and allow for change password and security answer
@bp.route("/<username>", methods=("GET", "POST"))
@login_required
def user_profile(username):
    # for POST method, only used for password change
    if request.method == "POST":
        if request.form.get("changePasswordBtn"):
            return change_password(username)
        elif request.form.get('changeSecurityAnswerBtn'):
            return change_security_answer(username)

    # for GET method, user only allows to access their own profile
    else:
        if g.user[constants.USERNAME] == username:
            modified_answer = False if not g.user[constants.MODIFIED_ANSWER] else True
            return render_template("user/profile.html", username=username, security_answer=modified_answer)
        else:
            flash("Cannot access other user's profile", constants.ERROR)
            return redirect(url_for("detection.detect"))


# create user logic
@bp.route("/create", methods=["POST"])
@login_required
@login_admin_required
def create_user():
    response, _ = register_worker.work()
    if response["success"]:
        flash("Successfully created user", constants.INFO)
    else:
        flash(response["error"]["message"], constants.ERROR)
    return redirect(url_for("user.user_management"))


# delete user logic
@bp.route("/delete", methods=["POST"])
@login_required
@login_admin_required
def delete_user():
    db_conn = get_conn()
    cursor = db_conn.cursor()
    username = request.form.get("username")
    try:
        sql_stmt = "SELECT * FROM user WHERE username='{}'".format(username)
        cursor.execute(sql_stmt)
        if not cursor.fetchone():
            db_conn.commit()
            flash("No user exist in the database", constants.ERROR)
            return redirect(url_for("user.user_management"))
        sql_stmt = "DELETE FROM user WHERE username='{}'".format(username)
        cursor.execute(sql_stmt)
        # remove all user uploaded images
        if constants.IS_REMOTE:
            # remove the images stored in S3 as well
            s3_client = session.client("s3")
            response = delete_user_images_s3(s3_client, username)
            # if there's still something to delete
            while response.get("IsTruncated"):
                response = delete_user_images_s3(s3_client, username)
        else:
            user_image_folder = constants.USER_FOLDER.format(username)
            if os.path.exists(user_image_folder):
                shutil.rmtree(user_image_folder)
    except ClientError as ce:
        db_conn.rollback()
        flash("Failed to delete images in S3", constants.ERROR)
        return redirect(url_for("user.user_management"))
    except Exception as e:
        db_conn.rollback()
        flash("Unexpected error {}".format(e), constants.ERROR)
        return redirect(url_for("user.user_management"))
    else:
        db_conn.commit()
        flash("Successfully deleted user with username {}".format(username), constants.INFO)
        return redirect(url_for("user.user_management"))


# helper method for the change password logic
def change_password(username):
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    new_password_confirm = request.form.get("new_password_confirm")
    if not old_password or not new_password or not new_password_confirm:
        flash("Please provide old password, new password and confirm new password", constants.ERROR)
        return redirect(request.url)

    if new_password != new_password_confirm:
        flash("Please make sure the new password and confirm new password are the same", constants.ERROR)
        return redirect(request.url)
    elif new_password == old_password:
        flash("New password is the same as old password, please change", constants.ERROR)
        return redirect(request.url)

    # make queries to the SQL DB to modify the user record
    try:
        db_conn = get_conn()
        cursor = db_conn.cursor()
        # hash_pwd = generate_hashed_password(old_password)
        sql_stmt = "SELECT * FROM user WHERE username='{}'".format(username)
        cursor.execute(sql_stmt)
        user = cursor.fetchone()
        if not verify_password(user[constants.PASSWORD], old_password):
            db_conn.commit()
            flash("Incorrect password", constants.ERROR)
            return redirect(request.url)
        new_hash_pwd = encrypt_credentials(new_password)
        sql_stmt = "UPDATE user SET password='{}' WHERE username='{}'".format(new_hash_pwd, username)
        cursor.execute(sql_stmt)
        db_conn.commit()
    except Exception as e:
        flash("Unexpected error {}".format(e), constants.ERROR)
        return redirect(request.url)
    else:
        flash("Password is updated successfully", constants.INFO)
        return render_template("user/profile.html", username=username)


# helper method for the change security answer logic
def change_security_answer(username):
    # confirm the input are the same
    new_securityanswer = request.form.get("new_securityAnswer")
    new_securityanswer_confirm = request.form.get("new_securityAnswer_confirm")
    if not new_securityanswer or not new_securityanswer_confirm:
        flash("Please provide new security answer and confirm new security answer when making changes", constants.ERROR)
        return redirect(request.url)
    if new_securityanswer != new_securityanswer_confirm:
        flash("Please make sure the new security answer and confirm new security answer are the same", constants.ERROR)
        return redirect(request.url)

    try:
        new_hash_pwd = encrypt_credentials(new_securityanswer)
        db_conn = get_conn()
        cursor = db_conn.cursor()
        if g.user[constants.MODIFIED_ANSWER]:
            old_securityanswer = request.form.get("old_securityAnswer")
            if not old_securityanswer:
                flash("Please provide old security answer", constants.ERROR)
            if not verify_password(g.user[constants.SECURITY_ANSWER], old_securityanswer):
                db_conn.commit()
                flash("Incorrect security answer", constants.ERROR)
                return redirect(request.url)
        sql_stmt = "UPDATE user SET security_answer='{}' WHERE username='{}'".format(new_hash_pwd, username)
        cursor.execute(sql_stmt)
        sql_stmt = "UPDATE user SET modified_answer='1' WHERE username='{}'".format(username)
        cursor.execute(sql_stmt)
        db_conn.commit()
    except Exception as e:
        flash("Unexpected error {}".format(e), constants.ERROR)
        return redirect(request.url)
    else:
        flash("Security answer is updated successfully", constants.INFO)
        return redirect(url_for("user.user_profile", username=username))


# delete the images from s3 bucket
def delete_user_images_s3(s3_client, username):
    response = s3_client.list_objects_v2(Bucket=constants.BUCKET_NAME, Prefix=username + "/")
    keys = {"Objects": [{"Key": file["Key"]} for file in response["Contents"]]}
    s3_client.delete_objects(Bucket=constants.BUCKET_NAME, Delete=keys)
    return response
