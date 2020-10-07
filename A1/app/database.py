import pymysql

db_conn = None
# will need to install mysql and set up user info
# run the schema.sql to set up the database with schema tables and initial data

# different DB configs for different environments
DATABASE_DEV_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "rootroot",
    "db": "ECE1779A1"
}
DATABASE_PROD_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "ece1779pass",
    "db": "ECE1779A1"
}


def init_db(env):
    global db_conn
    if env == "development":
        db_conn = pymysql.connect(**DATABASE_DEV_CONFIG)
    elif env == "production":
        db_conn = pymysql.connect(**DATABASE_PROD_CONFIG)


def close_db():
    db_conn.close()
