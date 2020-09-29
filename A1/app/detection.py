import os
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for

from FaceMaskDetection import pytorch_infer
from app import constants
from app.login import login_required

bp = Blueprint('detection', __name__, url_prefix='/detection')


@bp.route('/', methods=('GET', 'POST'))
@login_required
def detect():
    if request.method == "POST":
        # TODO: check file exists
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # TODO: save file based on the user
            filename = generate_file_name()
            # TODO: save to the designated location
            dest_path = constants.DEST_FOLDER + filename
            temp_file_path = os.path.join(constants.TEMP_FOLDER, filename)
            file.save(temp_file_path)
            pytorch_infer.main(temp_file_path, dest_path)
            os.remove(temp_file_path)
            # TODO: update the MySQL DB
            # TODO: back to the detection page and display the required message (upload status)
            return redirect(url_for("detection.detect"))

    return render_template("detection.html")


def generate_file_name():
    # TODO: based on the current user, generate the current user's information in file name
    return str(datetime.now()) + ".jpeg"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in constants.ALLOWED_EXTENSIONS
