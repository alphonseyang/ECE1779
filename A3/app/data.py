import boto3
from flask import flash, redirect, render_template, request, url_for
from validate_email import validate_email

from app import constants


def work():

    countries = get_supported_countries()
    return render_template("main.html", countries=countries)



def display():
    if request.method == "POST":
        country = request.form.get("country")
        startdate = request.form.get("startdate")
        enddate = request.form.get("enddate")
        if validate_date(startdate, enddate):
            get_prediction_data(country,startdate,enddate)
        else:
            return redirect(url_for(".data_config"))
    return render_template("display.html")


def get_supported_countries():
    # TODO: this should be dynamic
    return ["Canada", "China", "United States", "Japan", "South Korea",
            "United Kingdom", "France", "Germany", "Mexico", "India"]


def validate_date(startdate, enddate):
    start = startdate.split("/")
    end = enddate.split("/")
    if start[0] <= end[0] and start[1] <= end[1] and start[2] <= end[2]:
        return True
    else:
        flash("Invalid date input", constants.ERROR)


def get_prediction_data(country,startdate,enddate):
    session = boto3.Session(region_name="us-east-1")
    client = session.boto3.client('forecastquery')
    return None
