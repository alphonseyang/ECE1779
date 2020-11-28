import boto3
import json
from app import constants


# receive the SQS trigger and process the email to send
def lambda_handler(event, context):
    if len(event.get("Records", list())) == 0: return
    message = json.loads(event["Records"][0]["body"])
    country = message["country"]
    emails = message["emails"]
    freq = message["frequency"]
    email_sub, email_body = prepare_email(country, freq)
    ses = boto3.client("ses")
    for i in range(len(emails), constants.SEND_EMAIL_BATCH_SIZE):
        batch_emails = emails[i:i+constants.SEND_EMAIL_BATCH_SIZE]
        ses.send_email(
            Source=constants.SOURCE_EMAIL,
            Destination={"ToAddresses": batch_emails},
            Message={
                "Subject": {"Data": email_sub, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": email_body, "Charset": "UTF-8"}}
            }
        )


# download the prediction result and prepare email to user
def prepare_email(country, freq):
    pass
