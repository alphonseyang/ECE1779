import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Attr

SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/752103853538/subscription"
EMAIL_WORKER_BATCH_SIZE = 10000
SUBSCRIPTION_DDB_TABLE = "subscription"
sns = boto3.client("sns")
cloudwatch = boto3.client("cloudwatch")
forecast = boto3.client('forecastquery')
freq_days = {"daily": 1, "weekly": 7, "monthly": 30}

'''
scan the DDB subscription table to check for the emails that need to have the email sent 
(will need to create secondary index for mass customer situation in the future)
create sqs message and let worker do the work.
'''


def lambda_handler(event, context):
    freq = event.get("frequency", "daily")
    # emails_countries = get_emails_countries(freq)
    # for country in emails_countries:
    #     create_worker_tasks(country, emails_countries[country], freq)
    topic_arns = get_topic_arns(freq)
    counter = Counter()
    for arn in topic_arns:
        country = arn.split(":")[-1].split("-")[0].replace("_", " ")
        counter[country] += 1
        publish_message(arn, country, freq)
    for country in counter:
        subscription_metrics(country, freq, counter[country])


# get the topic arns that will need to publish new messages to the subscribed users
def get_topic_arns(freq):
    countries = get_supported_countries()
    topic_names = set([country.replace(" ", "_") + "-" + freq for country in countries])
    response = sns.list_topics()
    topic_arns = list()
    for topic in response.get("Topics", list()):
        should_remove = None
        for name in topic_names:
            if name in topic["TopicArn"]:
                topic_arns.append(topic["TopicArn"])
                should_remove = name
                break
        if should_remove:
            topic_names.remove(should_remove)
    return topic_arns


# publish message to the user
def publish_message(topic_arn, country, freq):
    today = datetime.utcnow().date()
    till = today + timedelta(days=freq_days[freq])
    start = str(datetime.combine(today, datetime.min.time()))
    end = str(datetime.combine(till, datetime.min.time()))
    start = start.split(" ")
    end = end.split(" ")
    start = start[0] + 'T' + start[1]
    end = end[0] + 'T' + end[1]
    response = forecast.query_forecast(
        ForecastArn='arn:aws:forecast:us-east-1:324985808241:forecast/a3_covid_global_forecast',
        StartDate=start,
        EndDate=end,
        Filters={
            "item_id": country
        },
    )
    prediction = response['Forecast']['Predictions']['p50'][-1]["Value"]
    sns.publish(
        TopicArn=topic_arn,
        Subject="Covid-19 Prediction for {} on {}".format(country, today),
        Message="The predicted Covid-19 case for {} in {} days will be {}".format(country, freq_days[freq], prediction)
    )


# keep track of the subscription metrics
def subscription_metrics(country, freq, num_msgs):
    cloudwatch.put_metric_data(
        MetricData=[{
            'MetricName': 'Requests',
            'Dimensions': [{
                'Name': 'Country',
                'Value': country,
            }, {
                "Name": "Frequency",
                "Value": freq
            }],
            'Timestamp': datetime.utcnow(),
            'Unit': 'Count',
            'Value': num_msgs
        }],
        Namespace='ECE1779/SUBSCRIPTION'
    )


def get_supported_countries():
    return ["Canada", "China ", "US", "Japan", "South Korea",
            "United Kingdom", "France", "Germany", "Mexico", "India"]


'''
Original design using SES service, which is not available for the educate account
keep the code just for reference
'''


# extract all the emails that need to have the email send
def get_emails_countries(freq):
    ddb = boto3.client("dynamodb")
    outcome = defaultdict(list)
    response = ddb.scan(
        TableName=SUBSCRIPTION_DDB_TABLE,
        FilterExpression=Attr("frequency").eq(freq)
    )
    for item in response.get("Items", list()):
        outcome[item["country"]["S"]].append(item["email"]["S"])
    return outcome


# create SQS message for worker to consume
def create_worker_tasks(country, emails, freq):
    sqs = boto3.client("ses")
    bulk = EMAIL_WORKER_BATCH_SIZE
    for i in range(len(emails), bulk):
        bulk_emails = emails[i:i + bulk]
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps({
                "country": country,
                "emails": bulk_emails,
                "frequency": freq
            })
        )
