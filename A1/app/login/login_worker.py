from flask import render_template, request

from app.database import db_conn


def work():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db_conn.cursor()
        sql_stmt = "SELECT * FROM user WHERE username='{}' AND password='{}'".format(username, password)
        cursor.execute(sql_stmt)
        a = list()
        for i in cursor:
            a.append(i)
        print(a)

    return render_template('login.html')
