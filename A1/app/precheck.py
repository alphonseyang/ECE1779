import functools

from flask import flash, g, redirect, url_for

from app import constants


# if already login, just redirect to detection, will not go to login page again unless log out
def already_login(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user:
            return redirect(url_for("detection.detect"))
        return view(**kwargs)

    return wrapped_view


# decorator method that force all not signed request to jump back to login page
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login.login"))
        return view(**kwargs)

    return wrapped_view


# decorator method that force all not signed request to jump back to login page
def login_admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user[constants.ROLE] == constants.USER:
            flash("You don't have permission to access user management page", constants.ERROR)
            return redirect(url_for("detection.detect"))
        return view(**kwargs)

    return wrapped_view
