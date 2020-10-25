import pymysql

from app import constants

'''
Database initialization implementation file
'''


db_conn = None
cur_config = None
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
DATABASE_PROD_LOCAL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "ece1779pass",
    "db": "ECE1779A1"
}
# TODO: use RDS endpoint here
DATABASE_PROD_RDS_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "ece1779pass",
    "db": "ECE1779A1"
}


# initialize the database connection when app creation
def init_db(env):
    global db_conn
    global cur_config
    # AWS RDS set up
    if constants.IS_REMOTE:
        db_conn = pymysql.connect(**DATABASE_PROD_RDS_CONFIG)
        cur_config = DATABASE_PROD_RDS_CONFIG
    # old local MySQL usage
    else:
        if env == "development":
            db_conn = pymysql.connect(**DATABASE_DEV_CONFIG)
            cur_config = DATABASE_DEV_CONFIG
        elif env == "production":
            db_conn = pymysql.connect(**DATABASE_PROD_LOCAL_CONFIG)
            cur_config = DATABASE_PROD_LOCAL_CONFIG


# get the connection, re-connect if necessary
def get_conn():
    global db_conn
    global cur_config
    if not db_conn or not db_conn.open:
        db_conn = pymysql.connect(**cur_config)
    return db_conn


# close database connection
def close_db():
    db_conn.close()
