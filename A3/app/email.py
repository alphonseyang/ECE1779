import boto3
from flask import flash, redirect, render_template, request, url_for
from validate_email import validate_email

from app import constants

ddb = boto3.client("dynamodb", region_name='us-east-1')


# main entry point to the email service
def work():
    if request.method == "POST":
        email_address = request.form.get("email")
        country = request.form.get("country")

        # validate the email input first
        if not validate_email(email_address):
            flash("Invalid Email Address", constants.ERROR)
            return redirect(url_for(".email_service"))

        if request.form.get("subscribe"):
            frequency = request.form.get("frequency", "daily")
            process_subscribe(email_address, country, frequency)
        else:
            process_unsubscribe(email_address, country)

        return redirect(url_for(".email_service"))

    else:
        countries = get_supported_countries()
        return render_template("email.html", countries=countries)


# helper method to subscribe the service
def process_subscribe(email_address, country, frequency):
    try:
        topic_arn = get_sns_topic(country, frequency)
        if not topic_arn:
            raise Exception("Failed to create/locate topic")
        sub_arn = register_email(email_address, topic_arn)
        ddb.put_item(
            TableName=constants.SUBSCRIPTION_DDB_TABLE,
            Item={
                "email": {"S": email_address},
                "country": {"S": country},
                "frequency": {"S": frequency},
                "sub_arn": {"S": sub_arn}
            }
        )
        flash("Subscription Email Sent, Please Confirm", constants.INFO)
    except Exception as e:
        print(e)
        flash("Failed to Subscribe, Please Try Again", constants.ERROR)


# helper method to unsubscribe the service
def process_unsubscribe(email_address, country):
    try:
        key = {
                "email": {"S": email_address},
                "country": {"S": country}
        }
        response = ddb.get_item(
            TableName=constants.SUBSCRIPTION_DDB_TABLE,
            Key=key
        )
        if not response.get("Item"):
            flash("Please Subscribe First", constants.ERROR)
            return
        error = deregister_email(response["Item"]["sub_arn"]["S"])
        if error:
            flash(error, constants.ERROR)
            return
        ddb.delete_item(
            TableName=constants.SUBSCRIPTION_DDB_TABLE,
            Key=key
        )
        flash("Successfully Unsubscribed", constants.INFO)
    except Exception as e:
        print(e)
        flash("Failed to Unsubscribe, Please Try Again", constants.ERROR)


# get the countries list that can be used
def get_supported_countries():
    # TODO: this should be dynamic
    return ["Canada", "China", "United States", "Japan", "South Korea",
            "United Kingdom", "France", "Germany", "Mexico", "India"]


# create topic if not exist
def get_sns_topic(country, freq):
    sns = boto3.client("sns")
    response = sns.list_topics()
    topics = response.get("Topics", list())
    new_topic = country.replace(" ", "_") + "-" + freq
    for topic in topics:
        if new_topic in topics:
            return topic
    response = sns.create_topic(Name=new_topic)
    return response.get("TopicArn")


# register an email to subscribe
def register_email(email, topic_arn):
    sns = boto3.client("sns")
    response = sns.subscribe(
        TopicArn=topic_arn,
        Protocol="email",
        Endpoint=email,
        ReturnSubscriptionArn=True
    )
    return response["SubscriptionArn"]


# deregister an email from SNS topic
def deregister_email(sub_arn):
    sns = boto3.client("sns")
    response = sns.get_subscription_attributes(SubscriptionArn=sub_arn)
    if response["Attributes"]["PendingConfirmation"] == "false":
        sns.unsubscribe(SubscriptionArn=sub_arn)
    else:
        return "Please confirm subscription before unsubscribe"
