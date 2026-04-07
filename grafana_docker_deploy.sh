#!/bin/bash

# copy ngrok config and authtoken to VM
scp -o StrictHostKeyChecking=no -i group_key -P 22000 ngrok-grafana.yml group09@paffenroth-23.dyn.wpi.edu:~/Case-Study-2/ngrok-grafana.yml
scp -o StrictHostKeyChecking=no -i group_key -P 22000 NGROK_AUTHTOKEN_GRAFANA group09@paffenroth-23.dyn.wpi.edu:~/Case-Study-2/NGROK_AUTHTOKEN_GRAFANA

ssh -o StrictHostKeyChecking=no -i group_key -p 22000 group09@paffenroth-23.dyn.wpi.edu << 'EOF'

cd ~/Case-Study-2
git stash
git pull
git switch main
git pull

# stop and remove old containers if they exist
docker stop grafana 2>/dev/null || true
docker rm grafana 2>/dev/null || true
docker stop ngrok-grafana 2>/dev/null || true
docker rm ngrok-grafana 2>/dev/null || true

# deploy grafana
docker run -d --name grafana --restart always -p 22095:3000 -v ~/Case-Study-2/grafana/provisioning:/etc/grafana/provisioning:ro -v grafana-storage:/var/lib/grafana -e GF_SECURITY_ADMIN_USER=admin -e GF_SECURITY_ADMIN_PASSWORD=admin -e 'GF_SERVER_ROOT_URL=%(protocol)s://%(domain)s/' grafana/grafana-oss

echo "grafana container started"

# deploy grafana ngrok
docker pull ngrok/ngrok

source NGROK_AUTHTOKEN_GRAFANA

# run ngrok with host networking so it can access grafana
docker run -d --name ngrok-grafana --net=host --restart always -e NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN_GRAFANA" -v ~/Case-Study-2/ngrok-grafana.yml:/etc/ngrok.yml:ro ngrok/ngrok:latest start --all --config /etc/ngrok.yml

echo "ngrok container started"

# check that it worked
docker ps --filter name=grafana --filter name=ngrok-grafana

EOF
