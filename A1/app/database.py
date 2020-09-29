from mysql import connector

db_conn = None
# will need to install mysql and set up user info
# run the schema.sql to set up the database with schema tables and initial data
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "rootroot",
    "database": "ECE1779A1"
}


def init_db():
    global db_conn
    db_conn = connector.connect(**DATABASE_CONFIG)


def close_db():
    db_conn.close()
