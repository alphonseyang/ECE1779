import boto3
import botocore
from flask import flash, redirect, render_template, request, url_for
from validate_email import validate_email

from io import StringIO
from app import constants
import pandas as pd
from datetime import datetime,date

def work():
    countries = get_supported_countries()
    return render_template("main.html", countries=countries)


def display():
    if request.method == "POST":
        if request.form.get("predict"):
            print("PREDICT")
            country = request.form.get("country")
            startdate = request.form.get("startdate")
            enddate = request.form.get("enddate")
            start = startdate.split("/")
            end = enddate.split("/")
            start = date(int(start[2]), int(start[0]), int(start[1]))
            end = date(int(end[2]), int(end[0]), int(end[1]))
            if start < end:
                response = get_prediction_data(country, start, end)
                if type(response) is str:
                    flash(response, constants.ERROR)
                    return redirect(url_for(".data_config"))
                else:
                    p10, p50, p90, timeseries = parse_prediction_data(response)
                    return render_template("display.html", history=False, timeseries=timeseries, p10=p10, p50=p50, p90=p90, country=country)
            else:
                return redirect(url_for(".data_config"))
        elif request.form.get("history"):
            print("HISTORY")
            country = request.form.get("historycountry")
            startdate = request.form.get("historystartdate")
            enddate = request.form.get("historyenddate")

            start = startdate.split("/")
            end = enddate.split("/")
            start = date(int(start[2]), int(start[0]), int(start[1]))
            end = date(int(end[2]), int(end[0]), int(end[1]))
            hisstart = date(2020, 1, 23)
            if start < end:
                if start < hisstart:
                    flash("Historical data starts from 2020-01-23", constants.ERROR)
                    return redirect(url_for(".data_config"))
                timeseries,case,csv_end= get_history_data(country, start, end)
                if not timeseries:
                    flash("Historical data end at "+csv_end, constants.ERROR)
                    return redirect(url_for(".data_config"))
                return render_template("display.html", history=True, timeseries=timeseries, cases=case, country=country)
    else:
        return redirect(url_for(".data_config"))
    return redirect(url_for(".data_config"))


def get_supported_countries():
    # TODO: this should be dynamic
    return ["Canada", "China ", "United States", "Japan", "South Korea",
            "United Kingdom", "France", "Germany", "Mexico", "India"]


def validate_date(startdate, enddate):

    if startdate < enddate:
        return True
    else:
        flash("Invalid date input", constants.ERROR)


def get_history_data(country, startdate, enddate):
    session = boto3.Session(region_name="us-east-1")
    client = session.client('s3')
    bucket_name = constants.S3_BUCKET
    object_key = 'covid_global_confirmed_cases.csv'
    csv_obj = client.get_object(Bucket=bucket_name, Key=object_key)
    body = csv_obj['Body']
    csv_string = body.read().decode('utf-8')
    df = pd.read_csv(StringIO(csv_string))
    countrydf = df.loc[df['country'] == country]
    csv_start = date(2020,1,23)
    csv_end = df.iloc[-1]['Country/Region']
    delta1 = (startdate- csv_start).days
    delta2 = (enddate-csv_start).days
    timeseries = []
    case = []
    print(delta2)
    print(len(countrydf))
    if delta2 < len(countrydf):
        t = countrydf.iloc[delta1:delta2 + 1]['Country/Region'].to_numpy()
        for i in range(len(t)):
            # value index, provides offset
            ti = t[i].split("-")
            tr = ti[0]+ti[1] + ti[2]
            timeseries.append(tr)
        case = df.iloc[delta1:delta2 + delta1 + 1]['cases'].tolist()

    return timeseries, case,csv_end


def get_prediction_data(country, startdate, enddate):
    session = boto3.Session(region_name="us-east-1")
    client = session.client('forecastquery')
    start = str(datetime.combine(startdate, datetime.min.time()))
    end = str(datetime.combine(enddate, datetime.min.time()))
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

    return p10,p50,p90,timeseries

