
from flask import Blueprint, g, redirect, render_template, request, session, url_for

from app.api import register_worker, upload_worker

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route("/register", methods=('GET', 'POST'))
def register():
    return register_worker.work()


@bp.route("/upload", methods=['POST'])
def upload():
    return upload_worker.work()
