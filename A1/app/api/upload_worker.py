from http import HTTPStatus

from flask import request

from app.detection import extract_mask_info, upload_file
from app.login import authenticate

'''
Upload API implementation file
'''


def work():
    username = request.form.get("username")
    password = request.form.get("password")
    file = request.files.get("file")
    response = {"success": False}
    status_code = HTTPStatus.BAD_REQUEST

    # check for the request parameters
    if not username or not password or not file:
        response["error"] = {"code": "MissingParameter",
                             "Message": "Please provide parameters username, password and file in the request"}
        return response, status_code

    # authenticate to ensure proper credentials
    error = authenticate(username, password)
    if error:
        response["error"] = {"code": "InvalidCredentials", "Message": error}
        return response, status_code

    # upload file and check the status
    file_data = file.read()
    error, output_info, _ = upload_file(file_data)
    if not error:
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        response["error"] = {"code": "UploadFailure", "Message": msg}
    else:
        status_code = HTTPStatus.OK
        response["success"] = True
        response["payload"] = extract_mask_info(output_info)

    return response, status_code
