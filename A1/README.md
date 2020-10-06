###How to SSH to EC2
1. cp {A1_path}/ECE1779A1KuangWangYang.pem ~/.ssh
2. chmod 400 ~/.ssh/ECE1779A1KuangWangYang.pem
3. ssh -i ~/.ssh/ECE1779A1KuangWangYang.pem ubuntu@52.91.41.105
4. ssh -i ~/.ssh/ECE1779A1KuangWangYang.pem ubuntu@52.91.41.105 -L 5901:localhost:5901 (this for if you want to connect via VNC)
5. Download VNC Viewer (VNC Viewer, Putty, Tiger VNC or etc.) localhost:5901, password: ecc1779pass