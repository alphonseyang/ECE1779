from threading import Thread

from flask import Flask

from app import auto_scaler, manager

'''
main app factory that creates the flask app
'''


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = "ECE1779"

    from app import manager
    app.register_blueprint(manager.bp)

    # initialize during app creation
    manager.app_initialization()

    # start the auto-scaler as the background thread
    thread = Thread(target=auto_scaler.start)
    thread.daemon = True
    thread.start()

    return app
