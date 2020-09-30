import os
from datetime import datetime

import requests
from flask import Blueprint, flash, g, render_template, request, redirect, url_for

from FaceMaskDetection import pytorch_infer
from app import constants
from app.login import login_required

bp = Blueprint('detection', __name__, url_prefix='/detection')


# main detection method that calls the AI part and save records
@bp.route('/', methods=('GET', 'POST'))
@login_required
def detect():
    if request.method == "POST":
        # ensure image is provided
        if 'file' not in request.files and 'online_file' not in request.form:
            flash("No file or URL provided")
            return redirect(request.url)

        # determine which type of upload
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            file_name = file.filename
            file_data = file.read()
            if not allowed_file(True, file_name=file_name, file_size=len(file_data)):
                flash("Image doesn't meet the requirement")
                return redirect(request.url)
        else:
            url = request.form['url']
            response = requests.get(url)
            data_type = response.headers.get('content-type')
            if not response.ok:
                flash("Online image doesn't exist")
                return redirect(request.url)
            file_data = response.content
            if not allowed_file(False, data_type=data_type, file_size=len(file_data)):
                flash("File doesn't meet the requirement")
                return redirect(request.url)

        # pass all check, upload the file
        _, msg, _ = upload_file(file_data)
        flash(msg)
        return redirect(request.url)

    return render_template("detection.html")


# main logic to upload file and save records
def upload_file(file_data):
    success = False
    output_info = None
    # TODO: (not sure if we need) save the original file based on the user
    output_file_name = generate_file_name()
    # TODO: save to the designated location
    dest_path = constants.DEST_FOLDER + output_file_name
    temp_file_path = os.path.join(constants.TEMP_FOLDER, output_file_name)
    try:
        open(temp_file_path, 'wb').write(file_data)
        output_info = pytorch_infer.main(temp_file_path, dest_path)
        os.remove(temp_file_path)
        # TODO: update the MySQL DB
        # TODO: back to the detection page and display the required message (upload status)
    except Exception as e:
        msg = "Unexpected error {}".format(e)
    else:
        msg = "Successfully detected file"
        success = True
    return success, msg, output_info


# generate file name based on the current user name and time
def generate_file_name():
    username = g.user[constants.USERNAME]
    file_name = "{}-{}.jpeg".format(datetime.now(), username)
    return file_name


# check file to ensure the sizing and format
def allowed_file(is_local, file_name=None, file_size=0, data_type=''):
    # TODO: check file size as well
    if is_local:
        return '.' in file_name and file_name.rsplit('.', 1)[1].lower() in constants.ALLOWED_EXTENSIONS
    else:
        return '/' in data_type and data_type.split('/')[1].lower() in constants.ALLOWED_EXTENSIONS
