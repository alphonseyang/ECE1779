from flask import Flask

'''
main app factory that creates the flask app
'''


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    return app
