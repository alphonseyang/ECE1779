from flask import render_template


def work():
    return render_template("main.html", var=2)
