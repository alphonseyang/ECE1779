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