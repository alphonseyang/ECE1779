
from flask import request

from app import constants
from app.database import db_conn


def work():
    response = {"success": False}
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db_conn.cursor()

        if username in constants.RESERVED_NAMES:
            response["error"] = {"code": "Reserved Username",
                                 "Message": "Username is reserved"}
            return response

        error = None
        sql_stmt = "SELECT * FROM user WHERE username='{}' ".format(username)
        cursor.execute(sql_stmt)

        if not username:
            response["error"] = {"code": "Missing field",
                                 "Message": "Username is required"}
            return response

        elif not password:
            response["error"] = {"code": "Missing field",
                                 "Message": "password is required"}
        elif cursor.fetchone() is not None:
            response["error"] = {"code": "User already existed",
                                 "Message": "Username is already registered"}
        # TODO: hash password
        insert_stmt = 'INSERT INTO user (username, password,role) VALUES ("{}", "{}","user")'.format(username, password)
        if error is None:
            cursor.execute(insert_stmt)
            db_conn.commit()
            response["success"] = True
            return response

    return response
