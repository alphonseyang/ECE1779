import os
from datetime import datetime

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
        if 'file' not in request.files:
            flash("Failed to find file")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("File has no name")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # TODO: (not sure if we need) save the original file based on the user
            filename = generate_file_name()
            # TODO: save to the designated location
            dest_path = constants.DEST_FOLDER + filename
            temp_file_path = os.path.join(constants.TEMP_FOLDER, filename)
            try:
                file.save(temp_file_path)
                pytorch_infer.main(temp_file_path, dest_path)
                os.remove(temp_file_path)
                # TODO: update the MySQL DB
                # TODO: back to the detection page and display the required message (upload status)
            except Exception as e:
                flash("Unexpected error {}".format(e))
            else:
                flash("Successfully detected file")
            return redirect(url_for("detection.detect"))

    return render_template("detection.html")


# generate file name based on the current user name and time
def generate_file_name():
    username = g.user[constants.USERNAME]
    file_name = "{}-{}.jpeg".format(datetime.now(), username)
    return file_name


# check file to ensure the sizing and format
def allowed_file(filename):
    # TODO: check file size as well
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in constants.ALLOWED_EXTENSIONS
