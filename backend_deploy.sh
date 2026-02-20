#!/bin/bash

# clear the shared key
ssh-keygen -f ~/.ssh/known_hosts -R "[paffenroth-23.dyn.wpi.edu]:22009"

ssh -p 22009 group09@paffenroth-23.dyn.wpi.edu << EOF

# wipe and rebuild authorized_keys with only our keys
> ~/.ssh/authorized_keys
echo "$(cat ARTEM_KEY)" >> ~/.ssh/authorized_keys
echo "$(cat CONNOR_KEY)" >> ~/.ssh/authorized_keys
echo "$(cat KARISH_KEY)" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# clone repo
git clone https://github.com/MLOPS26/Case-Study-2.git ~/Case-Study-2

# install deps
cd ~/Case-Study-2
~/.local/bin/uv sync

# deploy service
sudo cp services/backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now backend

# watchdog cron
sudo bash services/add-cron-backend.sh

EOF
