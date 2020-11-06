import pymysql

'''
Database initialization implementation file
'''

# will need to install mysql and set up user info
# run the schema.sql to set up the database with schema tables and initial data

DATABASE_PROD_RDS_CONFIG = {
    "host": "ece1779yangkuangwang-db.cysdmtlxkjur.us-east-1.rds.amazonaws.com",
    "port": 3306,
    "user": "root",
    "password": "ECE1779pass.",
    "db": "ECE1779"
}


# get the connection, re-connect if necessary
def get_conn():
    db_conn = pymysql.connect(**DATABASE_PROD_RDS_CONFIG)
    return db_conn
