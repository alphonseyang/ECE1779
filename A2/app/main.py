from flask import Blueprint, render_template


bp = Blueprint("main", __name__, url_prefix="/")

'''
Main entry point to the manager app, dispatch work to the other modules
'''


# main dispatcher to the other functionality
@bp.route("/", methods=("GET", "POST"))
def main():

    return render_template("main.html")
