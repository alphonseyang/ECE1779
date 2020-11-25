import boto3
from flask import flash, redirect, render_template, request, url_for
from validate_email import validate_email

from app import constants

ddb = boto3.client("dynamodb")


# main entry point to the email service
def work():
    if request.method == "POST":
        email_address = request.form.get("email")

        # validate the email input first
        if not validate_email(email_address):
            flash("Invalid Email Address", constants.ERROR)
            return redirect(url_for(".email_service"))

        if request.form.get("subscribe"):
            frequency = request.form.get("frequency", "1w")
            process_subscribe(email_address, frequency)
        else:
            process_unsubscribe(email_address)

        return redirect(url_for(".email_service"))

    else:
        return render_template("email.html")


# helper method to subscribe the service
def process_subscribe(email_address, frequency):
    pass


# helper method to unsubscribe the service
def process_unsubscribe(email_address):
    pass
