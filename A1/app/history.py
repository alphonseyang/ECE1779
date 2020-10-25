from flask import Blueprint, flash, render_template, redirect, request

from app import constants
from app.database import get_conn
from app.precheck import login_required

bp = Blueprint("history", __name__, url_prefix="/history")

'''
upload history logic implementation file
'''


@bp.route("/history/<username>")
@login_required
def history(username):
    try:
        # query the images for user
        db_conn = get_conn()
        cursor = db_conn.cursor()
        query = '''SELECT user.username, image.category, image.image_path, image.image_id , image.created_at FROM user JOIN image 
        ON user.username = image.username WHERE user.username = "{}" Order by image.created_at DESC
        '''.format(username)
        cursor.execute(query)
        images = cursor.fetchall()
        db_conn.commit()

        # separate the user images based on the category
        no_faces_detected = []
        all_faces_wear_masks = []
        no_faces_wear_masks = []
        partial_faces_wear_masks = []
        for image in images:
            if image[1] == constants.NO_FACES_DETECTED:
                no_faces_detected.append(image)
            elif image[1] == constants.ALL_FACES_WEAR_MASKS:
                all_faces_wear_masks.append(image)
            elif image[1] == constants.NO_FACES_WEAR_MASKS:
                no_faces_wear_masks.append(image)
            elif image[1] == constants.PARTIAL_FACES_WEAR_MASKS:
                partial_faces_wear_masks.append(image)
        category_map = {
            "No face detected in image": no_faces_detected,
            "All faces from image are wearing masks": all_faces_wear_masks,
            "No faces from image are wearing masks": no_faces_wear_masks,
            "Only some faces from image are wearing masks": partial_faces_wear_masks
        }

        # pass in the image lists to the view
        return render_template("history/history.html",
                               category_map=category_map,
                               is_remote=constants.IS_REMOTE)
    except Exception as e:
        flash("Unexpected error {}".format(e), constants.ERROR)
        return redirect(request.url)
