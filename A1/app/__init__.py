from threading import Thread

from flask import Flask, redirect, url_for

from app import aws_helper, constants

'''
main app factory that creates the flask app
'''


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # initialize the database connection based on the environment variable
    from app import database
    database.init_db(app.config["ENV"])

    # use a constant secret key for database for now
    # for real case, probably use the CMK stored in AWS SSM Parameter Store and retrieve from there
    app.secret_key = "ECE1779"

    # register the blueprint to associate with a separate file and path
    from app import api
    app.register_blueprint(api.bp)
    from app import login
    app.register_blueprint(login.bp)
    from app import detection
    app.register_blueprint(detection.bp)
    from app import user
    app.register_blueprint(user.bp)
    from app import history
    app.register_blueprint(history.bp)

    # auto forward the root index to login
    @app.route("/")
    def root_index():
        return redirect(url_for("login.login"))

    # start the auto-scaler as the background thread
    instance_id = aws_helper.get_instance_id()
    thread = Thread(target=aws_helper.collect_requests_count, args=(instance_id,))
    thread.daemon = True
    thread.start()

    return app

