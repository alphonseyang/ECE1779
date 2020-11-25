from flask import Flask

from app import data, email

'''
main app factory that creates the flask app
'''


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.secret_key = "ECE1779"

    @app.route("/")
    def data_display():
        return data.work()

    @app.route("/email", methods=["GET", "POST"])
    def email_service():
        return email.work()

    return app
