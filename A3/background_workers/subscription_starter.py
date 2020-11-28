import json
from collections import defaultdict

import boto3
from boto3.dynamodb.conditions import Attr

from app import constants

'''
scan the DDB subscription table to check for the emails that need to have the email sent 
(will need to create secondary index for mass customer situation in the future)
create sqs message and let worker do the work.
'''


def lambda_handler(event, context):
    freq = event.get("frequency", "daily")
    emails_countries = get_emails_countries(freq)
    for country in emails_countries:
        create_worker_tasks(country, emails_countries[country], freq)


# extract all the emails that need to have the email send
def get_emails_countries(freq):
    ddb = boto3.client("dynamodb")
    outcome = defaultdict(list)
    response = ddb.scan(
        TableName=constants.SUBSCRIPTION_DDB_TABLE,
        FilterExpression=Attr("frequency").eq(freq)
    )
    for item in response.get("Items", list()):
        outcome[item["country"]["S"]].append(item["email"]["S"])
    return outcome


# create SQS message for worker to consume
def create_worker_tasks(country, emails, freq):
    sqs = boto3.client("ses")
    bulk = constants.EMAIL_WORKER_BATCH_SIZE
    for i in range(len(emails), bulk):
        bulk_emails = emails[i:i+bulk]
        sqs.send_message(
            QueueUrl=constants.SQS_QUEUE_URL,
            MessageBody=json.dumps({
                "country": country,
                "emails": bulk_emails,
                "frequency": freq
            })
        )
