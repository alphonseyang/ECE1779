import os
import re
import uuid
from datetime import datetime

import requests
from PIL import Image
from botocore.exceptions import ClientError
from flask import Blueprint, flash, g, render_template, request, redirect, url_for

from FaceMaskDetection import pytorch_infer
from app import constants
from app.aws_helper import session
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
            url = request.form.get("url")
            # validate URL before calling request.get
            if not url or not validate_url(url):
                flash("Invalid Online Image URL", constants.ERROR)
                return redirect(request.url)
            try:
                response = requests.get(url)
            except Exception:
                flash("Failed to access link", constants.ERROR)
                return redirect(request.url)
            else:
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
        SELECT processed_image_path, unprocessed_image_path, thumbnail_image_path, category, num_faces, 
        num_masked, num_unmasked, username FROM image WHERE image_id="{}"
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

    return render_template("detection/show.html",
                           image_record=image_record,
                           category_map=constants.CATEGORY_MAP,
                           is_remote=constants.IS_REMOTE)


# main logic to upload file and save records
def upload_file(file_data):
    # file directory processing
    output_info = None
    output_file_name, image_id = generate_file_name()
    username = g.user[constants.USERNAME]
    processed_path = os.path.join(constants.PROCESSED_FOLDER.format(username), output_file_name)
    original_path = os.path.join(constants.UNPROCESSED_FOLDER.format(username), output_file_name)
    thumbnail_path = os.path.join(constants.THUMBNAIL_FOLDER.format(username), output_file_name)

    # make directory if not exist to prevent issue
    if not os.path.exists(constants.PROCESSED_FOLDER.format(username)):
        os.makedirs(constants.PROCESSED_FOLDER.format(username))
    if not os.path.exists(constants.UNPROCESSED_FOLDER.format(username)):
        os.makedirs(constants.UNPROCESSED_FOLDER.format(username))
    if not os.path.exists(constants.THUMBNAIL_FOLDER.format(username)):
        os.makedirs(constants.THUMBNAIL_FOLDER.format(username))

    try:
        # store the original file and do the detection
        open(original_path, "wb").write(file_data)
        image = Image.open(original_path)
        image.thumbnail((80, 80))
        image.save(thumbnail_path)
        output_info = pytorch_infer.main(original_path, processed_path)

        # for easier switch between local dev and prod usage
        if constants.IS_REMOTE:
            paths = {"processed": processed_path, "original": original_path, "thumbnail": thumbnail_path}
            paths = store_image_s3(paths)
            processed_path = paths["processed"]
            original_path = paths["original"]
            thumbnail_path = paths["thumbnail"]
        else:
            processed_path = processed_path[len(constants.STATIC_PREFIX):]
            original_path = original_path[len(constants.STATIC_PREFIX):]
            thumbnail_path = thumbnail_path[len(constants.STATIC_PREFIX):]

        # insert the record into the SQL DB
        mask_info = extract_mask_info(output_info)
        sql_stmt = '''
        INSERT INTO image (image_id, processed_image_path, unprocessed_image_path, thumbnail_image_path, category, 
        num_faces, num_masked, num_unmasked, username) VALUES ("{}", "{}", "{}", "{}", {}, {}, {}, {}, "{}")
        '''.format(image_id, processed_path, original_path, thumbnail_path, classify_image_category(mask_info), mask_info.get("num_faces", 0),
                   mask_info.get("num_masked", 0), mask_info.get("num_unmasked", 0), g.user[constants.USERNAME])
        db_conn = get_conn()
        cursor = db_conn.cursor()
        cursor.execute(sql_stmt)
        db_conn.commit()

    except ClientError as ce:
        error = "Failed to upload file to S3"
        return error, output_info, None
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


# validate url based on the regular expression
def validate_url(url):
    regex = r'^[a-z]+://(?P<host>[^/:]+)(?P<port>:[0-9]+)?(?P<path>\/.*)?$'
    return True if re.match(regex, url) else False


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


# upload the processed file to s3 and return the stored location
def store_image_s3(paths):
    s3_client = session.client("s3")
    result = dict()
    for image_type, path in paths.items():
        image_data = open(path, "rb").read()
        key_name = "{}/{}/{}".format(g.user[constants.USERNAME], image_type, path.split("/")[-1])
        # allow access for the s3 object in order to be displayed properly
        result[image_type] = "https://{}.s3.amazonaws.com/{}".format(constants.BUCKET_NAME, key_name)
        s3_client.put_object(Bucket=constants.BUCKET_NAME, Key=key_name, Body=image_data, ACL='public-read')
        # remove local stored processed image
        os.remove(path)
    return result
