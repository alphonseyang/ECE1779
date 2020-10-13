from flask import Blueprint

from app.api import register_worker, upload_worker

'''
Module init file that declares the API methods
'''


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/register", methods=["POST"])
def register():
    return register_worker.work()


@bp.route("/upload", methods=["POST"])
def upload():
    return upload_worker.work()
