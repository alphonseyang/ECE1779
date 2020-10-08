from http import HTTPStatus

from flask import request, redirect, url_for

from app import constants
from app.database import db_conn


def work():
    if request.method == 'POST':
        response = {"success": False}
        status_code = HTTPStatus.BAD_REQUEST
        username = request.form.get('username')
        password = request.form.get('password')

        # request validation before doing actual work
        if not username:
            response["error"] = {"code": "MissingParameter",
                                 "Message": "Please provide username in request"}
            return response, status_code
        elif not password:
            response["error"] = {"code": "MissingParameter",
                                 "Message": "Please provide password in request"}
            return response, status_code
        elif username in constants.RESERVED_NAMES:
            response["error"] = {"code": "ReservedUsername",
                                 "Message": "The username provided is reserved"}
            return response, status_code

        try:
            # check if the user is registered or not
            cursor = db_conn.cursor()
            sql_stmt = "SELECT * FROM user WHERE username='{}' ".format(username)
            cursor.execute(sql_stmt)

            if cursor.fetchone() is not None:
                response["error"] = {"code": "UserAlreadyExists",
                                     "Message": "Username is already registered"}
                return response, status_code

            # TODO: hash password
            # create new user and insert into DB
            insert_stmt = 'INSERT INTO user (username, password,role) VALUES ("{}", "{}","user")'.format(username, password)
            cursor.execute(insert_stmt)
            db_conn.commit()

        except Exception as e:
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            response["error"] = {"code": "ServerError",
                                 "Message": "Unexpected Server Error {}".format(e)}
        else:
            status_code = HTTPStatus.OK
            response["success"] = True

        return response, status_code

