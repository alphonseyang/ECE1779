
from flask import Blueprint, g, redirect, render_template, request, session, url_for
from app import constants
from app.database import db_conn
from werkzeug.security import check_password_hash, generate_password_hash
def work():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db_conn.cursor()
        error = None
        sql_stmt = "SELECT * FROM user WHERE username='{}' ".format(username)
        cursor.execute(sql_stmt)
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif cursor.fetchone() is not None:
            error = 'User {} is already registered.'.format(username)
        #TODO: hash password 
        insert_stmt = 'INSERT INTO user (username, password,role) VALUES ("{}", "{}","user")'.format(username, password)
        if error is None:
            cursor.execute(insert_stmt)
            
            return redirect(url_for('login.login'))

        flash(error)

    return render_template('register.html')
