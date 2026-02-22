#!/bin/bash

chmod 600 group_key

# clear the shared key
ssh-keygen -f ~/.ssh/known_hosts -R "[paffenroth-23.dyn.wpi.edu]:22000"

ssh -i group_key -o StrictHostKeyChecking=no -p 22000 group09@paffenroth-23.dyn.wpi.edu << EOF

# wipe and rebuild authorized_keys with only our keys
> ~/.ssh/authorized_keys
echo "$(cat ARTEM_KEY)" >> ~/.ssh/authorized_keys
echo "$(cat CONNOR_KEY)" >> ~/.ssh/authorized_keys
echo "$(cat KARISH_KEY)" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# install bun
curl -fsSL https://bun.sh/install | bash

# clone repo
rm -rf ~/Case-Study-2
git clone https://github.com/MLOPS26/Case-Study-2.git ~/Case-Study-2

# install deps
cd ~/Case-Study-2/shrug-intelligence
~/.bun/bin/bun install

# deploy service
sudo cp ~/Case-Study-2/services/frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now frontend

# watchdog cron
sudo bash ~/Case-Study-2/services/add-cron-frontend.sh

EOF
