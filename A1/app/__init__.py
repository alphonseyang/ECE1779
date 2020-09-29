from flask import Flask


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_mapping(
    #     SECRET_KEY='dev',
    #     DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    # )
    #
    # if test_config is None:
    #     # load the instance config, if it exists, when not testing
    #     app.config.from_pyfile('config.py', silent=True)
    # else:
    #     # load the test config if passed in
    #     app.config.from_mapping(test_config)
    #
    # # ensure the instance folder exists
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # initialize the database connection
    from app import database
    database.init_db()

    # register the blueprint to associate with a separate file and path
    from app import api
    app.register_blueprint(api.bp)
    from app import login
    app.register_blueprint(login.bp)
    from app import detection
    app.register_blueprint(detection.bp)

    app.secret_key = "ECE1779A1"

    return app

