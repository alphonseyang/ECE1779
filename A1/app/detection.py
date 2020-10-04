import os
from datetime import datetime

import requests
from flask import Blueprint, flash, g, render_template, request, redirect

from FaceMaskDetection import pytorch_infer
from app import constants
from app.database import db_conn
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
        msg, _ = upload_file(file_data)
        flash(msg)
        return redirect(request.url)

    return render_template("detection/detection.html")


@bp.route("/<image_id>")
@login_required
def show_image(image_id):
    # TODO: get image based on the id
    # TODO: render the show view
    return ''


# main logic to upload file and save records
def upload_file(file_data):
    output_info = None
    output_file_name = generate_file_name()
    user_image_folder = constants.DEST_FOLDER + g.user[constants.USERNAME] + "/"
    if not os.path.exists(user_image_folder):
        os.makedirs(user_image_folder)
    dest_path = user_image_folder + output_file_name
    temp_file_path = os.path.join(constants.TEMP_FOLDER, output_file_name)
    try:
        # store the original file and do the detection
        open(temp_file_path, 'wb').write(file_data)
        output_info = pytorch_infer.main(temp_file_path, dest_path)
        os.remove(temp_file_path)

        # insert the record into the SQL DB
        mask_info = extract_mask_info(output_info)
        sql_stmt = '''
        INSERT INTO image (image_path, category, num_faces, num_masked, num_unmasked, username) 
        VALUES ("{}", {}, {}, {}, {}, "{}")
        '''.format(dest_path, classify_image_category(mask_info), mask_info.get("num_faces", 0),
                   mask_info.get("num_masked", 0), mask_info.get("num_unmasked", 0), g.user[constants.USERNAME])
        cursor = db_conn.cursor()
        cursor.execute(sql_stmt)
        db_conn.commit()

    except Exception as e:
        msg = "Unexpected error {}".format(e)
    else:
        msg = "Successfully detected file"
    return msg, output_info


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


def extract_mask_info(output_info):
    return {
        "num_faces": len(output_info),
        "num_masked": sum([1 for face in output_info if face[0] == 1]),
        "num_unmasked": sum([1 for face in output_info if face[0] == 0])
    }


# determine the category of the image
def classify_image_category(mask_info):
    num_faces = mask_info.get("num_faces", 0)
    num_masked = mask_info.get("num_masked", 0)
    if num_faces == 0:
        return constants.NO_FACES_DETECTED
    elif num_faces == num_masked:
        return constants.ALL_FACES_WEAR_MASKS
    elif num_masked == 0:
        return constants.NO_FACES_WEAR_MASKS
    else:
        return constants.PARTIAL_FACES_WEAR_MASKS
