from http import HTTPStatus

from flask import request

from app import constants
from app.database import get_conn
from app.login import encrypt_credentials

'''
Register API implementation file
'''


def work():
    response = {"success": False}
    status_code = HTTPStatus.BAD_REQUEST
    username = request.form.get("username")
    password = request.form.get("password")

    # request validation before doing actual work
    if not username:
        response["error"] = {"code": "MissingParameter",
                             "message": "Please provide username in request"}
        return response, status_code
    elif not password:
        response["error"] = {"code": "MissingParameter",
                             "message": "Please provide password in request"}
        return response, status_code
    elif username in constants.RESERVED_NAMES:
        response["error"] = {"code": "ReservedUsername",
                             "message": "The username provided is reserved"}
        return response, status_code

    try:
        # check if the user is registered or not
        db_conn = get_conn()
        cursor = db_conn.cursor()
        sql_stmt = "SELECT * FROM user WHERE username='{}' ".format(username)
        cursor.execute(sql_stmt)

        if cursor.fetchone() is not None:
            response["error"] = {"code": "UserAlreadyExists",
                                 "message": "Username is already registered"}
            db_conn.commit()
            return response, status_code

        # create new user and insert into DB
        hashed_pwd = encrypt_credentials(password)
        hashed_ans = encrypt_credentials("default")
        insert_stmt = "INSERT INTO user (username, password,role,security_answer) VALUES ('{}', '{}', '{}','{}')".format(username, hashed_pwd, constants.USER, hashed_ans)
        cursor.execute(insert_stmt)
        db_conn.commit()

    # in case of error, report error
    except Exception as e:
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        response["error"] = {"code": "ServerError",
                             "message": "Unexpected Server Error {}".format(e)}
    # otherwise return success message
    else:
        status_code = HTTPStatus.OK
        response["success"] = True

    # returns response body with the corresponding HTTP status code
    return response, status_code
