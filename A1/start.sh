#!/bin/bash

# go to the directory where host the files
cd ~/Desktop/ECE1779_Projects/ECE1779/A1

# make logs directory if not exist
mkdir -p logs

# remove log file if exist before
[ -e logs/access.log ] && rm logs/access.log
[ -e logs/error.log ] && rm logs/error.log

# start the flask app using the factory mode
# with the env set to production and localhost:5000
# set up the access log and error log accordingly
./venv/bin/gunicorn -w 4 "app:create_app()" -e FLASK_ENV=production -b 0.0.0.0:5000 --access-logfile logs/access.log --error-logfile logs/error.log