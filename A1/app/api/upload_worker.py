from flask import request

from app.detection import extract_mask_info, upload_file
from app.login import authenticate


def work():
    username = request.form.get('username')
    password = request.form.get('password')
    file = request.files.get('file')
    response = {"success": False}

    # check for the request parameters
    if not username or not password or not file:
        response["error"] = {"code": "MissingParameter",
                             "Message": "Please provide parameters username, password and file in the request"}
        return response

    # authenticate to ensure proper credentials
    error = authenticate(username, password)
    if error:
        response["error"] = {"code": "InvalidCredentials", "Message": error}
        return response

    # upload file and check the status
    file_data = file.read()
    msg, output_info, _ = upload_file(file_data)
    if not output_info:
        response["error"] = {"code": "UploadFailure", "Message": msg}
        return response

    response["success"] = True
    response["payload"] = extract_mask_info(output_info)
    return response
