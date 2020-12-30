import pymysql

from app import constants

'''
Database initialization implementation file
'''

# will need to install mysql and set up user info
# run the schema.sql to set up the database with schema tables and initial data

db_conn = None
cur_config = None
DATABASE_DEV_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "*****",
    "db": "*****"
}
DATABASE_PROD_RDS_CONFIG = {
    "host": "*****.*****.us-east-1.rds.amazonaws.com",
    "port": 3306,
    "user": "root",
    "password": "*****",
    "db": "*****"
}


def init_db():
    global db_conn, cur_config
    cur_config = DATABASE_PROD_RDS_CONFIG  # if constants.IS_REMOTE else DATABASE_DEV_CONFIG
    db_conn = pymysql.connect(**cur_config)


# get the connection, re-connect if necessary
def get_conn():
    global db_conn, cur_config
    if not db_conn or not db_conn.open:
        db_conn = pymysql.connect(**cur_config)
    return db_conn
