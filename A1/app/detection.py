import os
from datetime import datetime
import uuid
import requests
from flask import Blueprint, flash, g, render_template, request, redirect, url_for

from FaceMaskDetection import pytorch_infer
from app import constants
from app.database import db_conn
from app.login import login_required

bp = Blueprint("detection", __name__, url_prefix="/detection")


# main detection method that calls the AI part and save records
@bp.route("/", methods=("GET", "POST"))
@login_required
def detect():
    if request.method == "POST":
        # ensure image is provided
        if "file" not in request.files and "online_file" not in request.form:
            flash("No file or URL provided")
            return redirect(request.url)

        # determine which type of upload
        if "file" in request.files and request.files["file"].filename != "":
            file = request.files["file"]
            file_name = file.filename
            file_data = file.read()
            error = allowed_file(True, file_name=file_name, file_size=len(file_data))
            if error:
                flash("Image doesn't meet the requirement")
                return redirect(request.url)
        else:
            url = request.form["url"]
            response = requests.get(url)
            data_type = response.headers.get("content-type")
            if not response.ok:
                flash("Online image doesn't exist")
                return redirect(request.url)
            file_data = response.content
            error = allowed_file(False, data_type=data_type, file_size=len(file_data))
            if error:
                flash(error)
                return redirect(request.url)

        # pass all check, upload the file
        msg, output_info, image_id = upload_file(file_data)
        flash(msg)
        if output_info and image_id:
            return redirect(url_for("detection.show_image", image_id=image_id))
        else:
            return redirect(request.url)

    return render_template("detection/detection.html")


@bp.route("/<image_id>")
@login_required
def show_image(image_id):
    try:
        sql_stmt = '''
        SELECT image_path, category, num_faces, num_masked, num_unmasked, username FROM image
        WHERE image_id="{}"
        '''.format(image_id)
        cursor = db_conn.cursor()
        cursor.execute(sql_stmt)
        image_record = cursor.fetchone()
        db_conn.rollback()

        # if not found
        if not image_record:
            flash("Couldn't find the image")
            return redirect(url_for("detection.detect"))

        # prevent unwanted access from other user
        if image_record[-1] != g.user[constants.USERNAME]:
            flash("Not allowed to access the image uploaded by other user")
            return redirect(url_for("detection.detect"))

    except Exception as e:
        flash("Unexpected exception {}".format(e))
        return redirect(url_for("detection.detect"))

    return render_template("detection/show.html", image_record=image_record, category_map=constants.CATEGORY_MAP)


# main logic to upload file and save records
def upload_file(file_data):
    output_info = None
    output_file_name, image_id = generate_file_name()
    user_image_folder = constants.DEST_FOLDER + g.user[constants.USERNAME] + "/"
    dest_relative_path = os.path.join(user_image_folder, output_file_name)
    dest_store_path = os.path.join(constants.STATIC_PREFIX, dest_relative_path)
    temp_file_path = os.path.join(constants.TEMP_FOLDER, output_file_name)

    # make directory if not exist to prevent issue
    if not os.path.exists(os.path.join(constants.STATIC_PREFIX, user_image_folder)):
        os.makedirs(os.path.join(constants.STATIC_PREFIX, user_image_folder))
    if not os.path.exists(constants.TEMP_FOLDER):
        os.makedirs(constants.TEMP_FOLDER)

    try:
        # store the original file and do the detection
        open(temp_file_path, "wb").write(file_data)
        output_info = pytorch_infer.main(temp_file_path, dest_store_path)
        os.remove(temp_file_path)

        # insert the record into the SQL DB
        mask_info = extract_mask_info(output_info)
        sql_stmt = '''
        INSERT INTO image (image_id, image_path, category, num_faces, num_masked, num_unmasked, username) 
        VALUES ("{}", "{}", {}, {}, {}, {}, "{}")
        '''.format(image_id, dest_relative_path, classify_image_category(mask_info), mask_info.get("num_faces", 0),
                   mask_info.get("num_masked", 0), mask_info.get("num_unmasked", 0), g.user[constants.USERNAME])
        cursor = db_conn.cursor()
        cursor.execute(sql_stmt)
        db_conn.commit()

    except Exception as e:
        msg = "Unexpected error {}".format(e)
    else:
        msg = "Successfully detected file"
    return msg, output_info, image_id


# generate file name based on the current user name and time
def generate_file_name():
    username = g.user[constants.USERNAME]
    image_id = uuid.uuid4().hex
    file_name = "{}-{}-{}.jpeg".format(datetime.now(), username, image_id)
    return file_name, image_id


# check file to ensure the sizing and format
def allowed_file(is_local, file_name=None, file_size=0, data_type=""):
    if file_size > constants.TEN_MB:
        return "File size too large, please upload file smaller than 10 MB"
    if is_local and not ("." in file_name and file_name.rsplit(".", 1)[1].lower() in constants.ALLOWED_EXTENSIONS):
        return "Local file is not an image"
    elif not is_local and not ("/" in data_type and data_type.split("/")[1].lower() in constants.ALLOWED_EXTENSIONS):
        return "Online link is not an image"
    return None


# extract the mask info from the AI output
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
