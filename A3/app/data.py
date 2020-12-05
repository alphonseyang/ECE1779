import boto3
import botocore
from flask import flash, redirect, render_template, request, url_for
from validate_email import validate_email
import datetime

from app import constants


def work():
    countries = get_supported_countries()
    return render_template("main.html", countries=countries)


def display():
    if request.method == "POST":
        country = request.form.get("country")
        startdate = request.form.get("startdate")
        enddate = request.form.get("enddate")
        start = startdate.split("/")
        end = enddate.split("/")
        if validate_date(start, end):
            response = get_prediction_data(country, start, end)
            if type(response) is str:
                flash(response, constants.ERROR)
                return redirect(url_for(".data_config"))
            else:
                p10, p50, p90, timeseries = parse_prediction_data(response)
                return render_template("display.html",timeseries=timeseries,p10=p10,p50=p50,p90=p90,country=country)
        else:
            return redirect(url_for(".data_config"))
    return render_template("display.html")


def get_supported_countries():
    # TODO: this should be dynamic
    return ["Canada", "China", "United States", "Japan", "South Korea",
            "United Kingdom", "France", "Germany", "Mexico", "India"]


def validate_date(startdate, enddate):
    if startdate[0] <= enddate[0] and startdate[1] <= enddate[1] and startdate[2] <= enddate[2]:
        return True
    else:
        flash("Invalid date input", constants.ERROR)


def get_prediction_data(country, startdate, enddate):
    session = boto3.Session(region_name="us-east-1")
    client = session.client('forecastquery')
    start = str(datetime.datetime(int(startdate[2]), int(startdate[0]), int(startdate[1])))
    end = str(datetime.datetime(int(enddate[2]), int(enddate[0]), int(enddate[1])))
    start = start.split(" ")
    end = end.split(" ")
    start = start[0] + 'T' + start[1]
    end = end[0] + 'T' + end[1]
    err = None
    try:
        response = client.query_forecast(
            ForecastArn='arn:aws:forecast:us-east-1:324985808241:forecast/a3_covid_global_forecast',
            StartDate=start,
            EndDate=end,
            Filters={
                "item_id": country
            },
        )
        print(response)

    except client.exceptions.InvalidInputException as err:
        response = 'Error Message: {}'.format(err.response['Error']['Message'])

    finally:
        return response


def parse_prediction_data(response):
    f10 = response['Forecast']['Predictions']['p10']
    f50 = response['Forecast']['Predictions']['p50']
    f90 = response['Forecast']['Predictions']['p90']
    p10 = []
    p50 = []
    p90 = []
    timeseries = []
    for i in range(len(f10)):
        # value index, provides offset
        p10.append(f10[i]["Value"])
        p50.append(f50[i]["Value"])
        p90.append(f90[i]["Value"])
        t = f10[i]['Timestamp'].split("T")
        t = t[0].split("-")
        t = t[0]+ t[1] + t[2]
        timeseries.append(t)
    print(timeseries)
    return p10,p50,p90,timeseries
