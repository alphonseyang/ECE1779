from flask import Blueprint

from app.api import register_worker, upload_worker

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route("/register")
def register():
    return register_worker.work()


@bp.route("/upload")
def upload():
    return upload_worker.work()
