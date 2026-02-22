#!/bin/bash

# clear the shared key
ssh-keygen -f ~/.ssh/known_hosts -R "[paffenroth-23.dyn.wpi.edu]:22000"

ssh -i group_key -p 22000 group09@paffenroth-23.dyn.wpi.edu << EOF


# install nvim for the freak who uses it for the server
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz
sudo rm -rf /opt/nvim-linux-x86_64
sudo tar -C /opt -xzf nvim-linux-x86_64.tar.gz

# append to bashrc
>> export PATH="$PATH:/opt/nvim-linux-x86_64/bin" ~/.bashrc


# source out bashrc
source ~/.bashrc

#clone nvim config to config folder
git clone https://github.com/afrenkai/konfig.git ~/.config/nvim/


# wipe and rebuild authorized_keys with only our keys
> ~/.ssh/authorized_keys
echo "$(cat ARTEM_KEY)" >> ~/.ssh/authorized_keys
echo "$(cat CONNOR_KEY)" >> ~/.ssh/authorized_keys
echo "$(cat KARISH_KEY)" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# install bun
curl -fsSL https://bun.sh/install | bash

# clone repo
git clone https://github.com/MLOPS26/Case-Study-2.git ~/Case-Study-2

# install prod deps only
cd ~/Case-Study-2/shrug-intelligence
~/.bun/bin/bun install --production

# deploy service
sudo cp ~/Case-Study-2/services/frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now frontend

# watchdog cron
sudo bash ~/Case-Study-2/services/add-cron-frontend.sh

EOF
