from flask import Blueprint

from app.detection import detection_worker

bp = Blueprint('detection', __name__, url_prefix='/detection')


@bp.route('/', methods=('GET', 'POST'))
def detect():
    return detection_worker.work()
