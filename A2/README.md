### Initial Set up
1. python3 -m venv venv # make sure use at least python 3.7
2. source venv/bin/activate
3. pip install -r requirement.txt
4. config local venv with IDE https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html

### Run Flask on Local with development setup
1. make sure you are in venv, there should be a (venv) in your terminal. If not, run "source venv/bin/activate"
2. export PYTHONUNBUFFERED=1
3. export FLASK_APP=app
4. export FLASK_ENV=development
5. flask run

### Things to Notice
1. don't commit local dependency (venv folder)
2. don't commit the .idea local environment folder
3. add ignored files to .gitignore

### How to SSH to EC2
1. cp {A1_path}/keypair.pem ~/.ssh
2. chmod 400 ~/.ssh/keypair.pem
3. ssh -i ~/.ssh/keypair.pem ubuntu@{IP_ADDRESS}
4. ssh -i ~/.ssh/keypair.pem ubuntu@{IP_ADDRESS} -L 5901:localhost:5901 (this for if you want to connect via VNC)
5. Download VNC Viewer (VNC Viewer, Putty, Tiger VNC or etc.) localhost:5901, password: ecc1779pass

### How to use start.sh
Since the start.sh is designed to run on top of EC2 instance, so the path is written based on the path of project folder in A2
folder in EC2 instance. The start.sh creates the log files and then use the gunicorn to start the flask application in 
localhost:5000 with 1 worker (chose based on the t2.small vCPU numbers). The 5000 port will be exposed to the outside 
by the security group attached to the EC2 instance

### Enable Remote Mode Locally
1. change the IS_REMOTE to True in constants.py file
2. make sure you have the AWS credentials from Educate account in your ~/.aws/credentials file
3. start the RDS instance in AWS
4. start Flask app as usual
5. if unable to connect, make sure your IP is listed in the security group assigned to the RDS instance (rds-sg-1), use the existing one as an example