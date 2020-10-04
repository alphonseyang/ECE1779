
from flask import Blueprint

from app.api import register_worker, upload_worker

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route("/register", methods=['POST'])
def register():
    return register_worker.work()


@bp.route("/upload", methods=['POST'])
def upload():
    return upload_worker.work()
