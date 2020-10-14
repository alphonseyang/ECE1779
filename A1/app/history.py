import os
from datetime import datetime
import uuid
import requests
from flask import Blueprint, flash, g, render_template, request, redirect, url_for

from FaceMaskDetection import pytorch_infer
from app import constants
from app.database import db_conn
from app.precheck import login_required
bp = Blueprint('history', __name__, url_prefix='/history')

@bp.route("/upload_history/<username>", methods=('GET', 'POST'))
@login_required
def upload_history(username):
    cursor = db_conn.cursor()

    query = "select user.username,image.category,image.image_path,image.image_id from user join image on user.username = image.username where user.username = '{}'".format(username)
    cursor.execute(query)
    uploaded_image0 = []
    uploaded_image1 = []
    uploaded_image2 = []
    uploaded_image3 = []

    x = cursor.fetchall()
    print(x)

    for i in x :
        if i[1] == 0 :
            uploaded_image0.append(i)
        elif i[1]  == 1 :
            uploaded_image1.append(i)
        elif i[1]  == 2 :
            uploaded_image2.append(i)
        elif i[1] == 3 :
            uploaded_image3.append(i)
        else:
            # unexpected error
            print("Error")

    print(uploaded_image0)
    print(uploaded_image1)
    print(uploaded_image2)
    print(uploaded_image3)


    return render_template("history/history.html", uploaded_image0=uploaded_image0,uploaded_image1=uploaded_image1,uploaded_image2=uploaded_image2,uploaded_image3=uploaded_image3)