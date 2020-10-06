### Initial Set up
1. python3 -m venv venv
2. source venv/bin/activate
3. pip install -r requirement.txt
4. config local venv with IDE https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html

### Run Flask
1. make sure you are in venv, there should be a (venv) in your terminal. If not, run "source venv/bin/activate"
2. sh start.sh

### Things to Notice
1. don't commit local dependency (venv folder)
2. don't commit the .idea local environment folder
3. add ignored files to .gitignore

###How to SSH to EC2
1. cp {A1_path}/ECE1779A1KuangWangYang.pem ~/.ssh
2. chmod 400 ~/.ssh/ECE1779A1KuangWangYang.pem
3. ssh -i ~/.ssh/ECE1779A1KuangWangYang.pem ubuntu@{IP_ADDRESS}
4. ssh -i ~/.ssh/ECE1779A1KuangWangYang.pem ubuntu@{IP_ADDRESS} -L 5901:localhost:5901 (this for if you want to connect via VNC)
5. Download VNC Viewer (VNC Viewer, Putty, Tiger VNC or etc.) localhost:5901, password: ecc1779pass

currently the IP_Address for EC2 instance is 54.165.66.86