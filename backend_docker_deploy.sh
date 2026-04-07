#!/bin/bash

# copy HF_TOKEN file to the VM
scp -o StrictHostKeyChecking=no -i group_key -P 22000 HF_TOKEN group09@paffenroth-23.dyn.wpi.edu:~/Case-Study-2/HF_TOKEN
scp -o StrictHostKeyChecking=no -i group_key -P 22000 NGROK_AUTHTOKEN group09@paffenroth-23.dyn.wpi.edu:~/Case-Study-2/NGROK_AUTHTOKEN
scp -o StrictHostKeyChecking=no -i group_key -P 22000 NGROK_AUTHTOKEN_BACKEND group09@paffenroth-23.dyn.wpi.edu:~/Case-Study-2/NGROK_AUTHTOKEN_BACKEND
scp -o StrictHostKeyChecking=no -i group_key -P 22000 ngrok.yml group09@paffenroth-23.dyn.wpi.edu:~/Case-Study-2/ngrok.yml
scp -o StrictHostKeyChecking=no -i group_key -P 22000 ngrok-backend.yml group09@paffenroth-23.dyn.wpi.edu:~/Case-Study-2/ngrok-backend.yml


ssh -o StrictHostKeyChecking=no -i group_key -p 22000 group09@paffenroth-23.dyn.wpi.edu << 'EOF'

# stop and remove old containers if they exist
docker stop cs3-backend 2>/dev/null || true
docker rm cs3-backend 2>/dev/null || true
docker stop prometheus 2>/dev/null || true
docker rm prometheus 2>/dev/null || true
docker stop ngrok 2>/dev/null || true
docker rm ngrok 2>/dev/null || true
docker stop ngrok-backend 2>/dev/null || true
docker rm ngrok-backend 2>/dev/null || true 

#clone or pull repo
if [ -d ~/Case-Study-2 ]; then
    cd ~/Case-Study-2
    git switch main
    git pull
else
    git clone https://github.com/MLOPS26/Case-Study-2.git ~/Case-Study-2
    cd ~/Case-Study-2
fi

# DEPLOY BACKEND

# build the backend image from repo root
docker build -t cs3-backend -f backend/Dockerfile .

# read HF_TOKEN
source HF_TOKEN


# run the backend container
docker run -d --name cs3-backend --restart always -p 22092:22092 -e HF_TOKEN="$HF_TOKEN" -v cs3-backend-uploads:/opt/app/uploads -v cs3-backend-db:/opt/app/db cs3-backend
echo "Backend container started!"

# DEPLOY PROMETHEUS

# run the prometheus container
docker run -d --name prometheus --restart always -p 22094:9090 -v ~/Case-Study-2/prometheus.yml:/etc/prometheus/prometheus.yml:ro prom/prometheus
echo "Prometheus container started!"

# DEPLOY NGROK

docker pull ngrok/ngrok

#read NGROK_AUTHTOKEN
source NGROK_AUTHTOKEN

#read NGROK_AUTHTOKEN_BACKEND
source NGROK_AUTHTOKEN_BACKEND


docker run -d --name ngrok --net=host --restart always -e NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN" -v ~/Case-Study-2/ngrok.yml:/etc/ngrok.yml:ro ngrok/ngrok:latest start --all --config /etc/ngrok.yml


docker run -d --name ngrok-backend --net=host --restart always -e NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN_BACKEND" -v ~/Case-Study-2/ngrok-backend.yml:/etc/ngrok-backend.yml:ro ngrok/ngrok:latest start --all --config /etc/ngrok.yml


echo "Ngrok containers started!"

# VERIFY RUNNING CONTAINERS
docker ps --filter name=cs3-backend --filter name=prometheus --filter name=ngrok

EOF
