
from flask import Blueprint, url_for, redirect

from app.api import register_worker, upload_worker

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route("/register", methods=['POST'])
def register():
    return register_worker.work()


@bp.route("/upload", methods=['POST'])
def upload():
    return upload_worker.work()


@bp.route("/register/user", methods=['POST'])
def registeruser():
    register()
    return redirect(url_for('user.user_management'))

