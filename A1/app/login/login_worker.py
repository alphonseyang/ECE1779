from flask import render_template, request

from app.database import db_conn


def work():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db_conn.cursor()

        # sample connection test, will need to remove later
        sql = "SELECT * FROM test"
        cursor.execute(sql)
        a = list()
        for i in cursor:
            a.append(i)
        print(a)

    return render_template('login.html')
