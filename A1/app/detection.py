import os
from datetime import datetime
import uuid
import requests
from flask import Blueprint, flash, g, render_template, request, redirect, url_for

from FaceMaskDetection import pytorch_infer
from app import constants
from app.database import get_conn
from app.precheck import login_required

bp = Blueprint("detection", __name__, url_prefix="/detection")

'''
Detection component for the image processing and display
'''


# main detection method that calls the AI part and save records
@bp.route("/", methods=("GET", "POST"))
@login_required
def detect():
    if request.method == "POST":
        # ensure image is provided
        if "file" not in request.files and "online_file" not in request.form:
            flash("No file or URL provided", constants.ERROR)
            return redirect(request.url)

        # check local file uploaded
        if "file" in request.files and request.files["file"].filename != "":
            file = request.files["file"]
            file_name = file.filename
            file_data = file.read()
            error = allowed_file(True, file_name=file_name, file_size=len(file_data))
            if error:
                flash("Image doesn't meet the requirement", constants.ERROR)
                return redirect(request.url)
        # check online link provided
        else:
            url = request.form["url"]
            response = requests.get(url)
            data_type = response.headers.get("content-type")
            if not response.ok:
                flash("Online image doesn't exist", constants.ERROR)
                return redirect(request.url)
            file_data = response.content
            error = allowed_file(False, data_type=data_type, file_size=len(file_data))
            if error:
                flash(error, constants.ERROR)
                return redirect(request.url)

        # pass all check, upload the file
        error, output_info, image_id = upload_file(file_data)
        if not error:
            flash("Successfully processed image", constants.INFO)
            return redirect(url_for("detection.show_image", image_id=image_id))
        else:
            flash(error, constants.ERROR)
            return redirect(request.url)

    return render_template("detection/detection.html")


# display image method
@bp.route("/<image_id>")
@login_required
def show_image(image_id):
    try:
        # query image data from the database
        sql_stmt = '''
        SELECT image_path, category, num_faces, num_masked, num_unmasked, username FROM image
        WHERE image_id="{}"
        '''.format(image_id)
        db_conn = get_conn()
        cursor = db_conn.cursor()
        cursor.execute(sql_stmt)
        image_record = cursor.fetchone()
        db_conn.commit()

        # if not found the image record
        if not image_record:
            flash("Couldn't find the image", constants.ERROR)
            return redirect(url_for("detection.detect"))

        # prevent unwanted access from other user
        if image_record[-1] != g.user[constants.USERNAME]:
            flash("Not allowed to access the image uploaded by other user", constants.ERROR)
            return redirect(url_for("detection.detect"))

    # error handling
    except Exception as e:
        flash("Unexpected exception {}".format(e), constants.ERROR)
        return redirect(url_for("detection.detect"))

    return render_template("detection/show.html", image_record=image_record, category_map=constants.CATEGORY_MAP)


# main logic to upload file and save records
def upload_file(file_data):
    # file directory processing
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
        db_conn = get_conn()
        cursor = db_conn.cursor()
        cursor.execute(sql_stmt)
        db_conn.commit()

    except Exception as e:
        error = "Unexpected error {}".format(e)
        return error, output_info, None
    else:
        return None, output_info, image_id


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
    num_faces = len(output_info)
    num_masked = sum([1 for face in output_info if face[0] == 0])
    return {
        "num_faces": num_faces,
        "num_masked": num_masked,
        "num_unmasked": num_faces - num_masked
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
