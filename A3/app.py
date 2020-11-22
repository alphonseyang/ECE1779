from flask import Flask
import email
import data

app = Flask(__name__)


@app.route("/")
def data_display():
    return data.work()


@app.route("/email", methods=["GET", "POST"])
def email_service():
    return email.work()


# We only need this for local development.
if __name__ == "__main__":
    app.run()
