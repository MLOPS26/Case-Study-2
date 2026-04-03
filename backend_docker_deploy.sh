#!/bin/bash

# clear the known hosts cache
ssh-keygen -f ~/.ssh/known_hosts -R "[paffenroth-23.dyn.wpi.edu]:22000"

ssh -i group_key -p 22000 group09@paffenroth-23.dyn.wpi.edu << 'EOF'

# stop existing systemd service if running
systemctl stop backend 2>/dev/null || true

# stop and remove old container if it exists
docker stop cs3-backend 2>/dev/null || true
docker rm cs3-backend 2>/dev/null || true

# clone or pull repo
if [ -d ~/Case-Study-2 ]; then
    cd ~/Case-Study-2
    git pull
else
    git clone https://github.com/MLOPS26/Case-Study-2.git ~/Case-Study-2
    cd ~/Case-Study-2
fi

# remove after wemerge to main
git switch docker

# build the backend image from repo root
docker build -t cs3-backend -f backend/Dockerfile .

# read HF_TOKEN
HF_TOKEN=$(cat HF_TOKEN)

# run the container
docker run -d --name cs3-backend --restart always -p 22092:22092 -e HF_TOKEN="$HF_TOKEN" -v cs3-backend-uploads:/opt/app/uploads -v cs3-backend-db:/opt/app/db cs3-backend

echo "backend container started"
docker ps --filter name=cs3-backend

EOF
