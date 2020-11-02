import json
from datetime import datetime, timedelta

import boto3
import dateutil.parser
import pytz
import requests

from app import constants

session = boto3.Session()
expires = datetime.utcnow().replace(tzinfo=pytz.utc)


# retrieve the credentials from the AWS IAM Role
def get_credentials():
    global session, expires
    if constants.IS_REMOTE:
        # retrieve AWS credentials
        response = requests.get(constants.ROLE_CREDENTIALS_URL)
        result = json.loads(response.content.decode())
        session = boto3.Session(
            aws_access_key_id=result["AccessKeyId"],
            aws_secret_access_key=result["SecretAccessKey"],
            aws_session_token=result["Token"]
        )
        expires = dateutil.parser.parse(result["Expiration"])
        print("INFO: successfully retrieved new credentials, expires at {}".format(expires))
    else:
        expires = datetime(2030, 1, 1).replace(tzinfo=pytz.utc)
        session = boto3.Session(region_name="us-east-1")



# if the credentials expires, renew
def check_credentials_expire():
    global session
    if datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(minutes=5) > expires:
        get_credentials()
