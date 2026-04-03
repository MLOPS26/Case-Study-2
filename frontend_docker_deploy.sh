#!/bin/bash

# clear the known hosts cache
ssh-keygen -f ~/.ssh/known_hosts -R "[paffenroth-23.dyn.wpi.edu]:22000"

ssh -i group_key -p 22000 group09@paffenroth-23.dyn.wpi.edu << 'EOF'

# stop existing systemd service if running
sudo systemctl stop frontend 2>/dev/null || true

# stop and remove old container if it exists
sudo docker stop cs3-frontend 2>/dev/null || true
sudo docker rm cs3-frontend 2>/dev/null || true

# clone or pull repo
if [ -d ~/Case-Study-2 ]; then
    cd ~/Case-Study-2
    git pull
else
    git clone https://github.com/MLOPS26/Case-Study-2.git ~/Case-Study-2
    cd ~/Case-Study-2
fi

# remove after we merge to main
git checkout docker

# build the frontend image from shrug-intelligence/ directory
sudo docker build -t cs3-frontend -f shrug-intelligence/Dockerfile shrug-intelligence/

# run the container
sudo docker run -d --name cs3-frontend --restart always -p 22091:22091 cs3-frontend

echo "frontend container started"
sudo docker ps --filter name=cs3-frontend

EOF
