import boto3
from flask import flash, redirect, render_template, request, url_for
from validate_email import validate_email

from app import constants

ddb = boto3.client("dynamodb")


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
        ddb.put_item(
            TableName=constants.SUBSCRIPTION_DDB_TABLE,
            Item={
                "email": {"S": email_address},
                "country": {"S": country},
                "frequency": {"S": frequency}
            }
        )
        flash("Successfully Subscribed", constants.INFO)
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
    return ["Canada", "China", "United States", "Japan", "South Korea", "United Kingdom", "France", "Germany", "Mexico", "India"]
