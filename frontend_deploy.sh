#!/bin/bash

export PORT=7009
export MACHINE=paffenroth-23.dyn.wpi.edu


#killing old runs
ssh-keygen -f "~/.ssh/known_hosts" -R "[paffenroth-23.dyn.wpi.edu]:21009"
rm -rf tmp

#temp dir
mkdir tmp


cat ARTEM_KEY >> ~/.ssh/authorized_keys
cat CONNOR_KEY >> ~/.ssh/authorized_keys
cat KARISH_KEY >> ~/.ssh/authorized_keys

chmod 600 ~/.ssh/authorized_keys

ls -l ~/.ssh/authorized_keys

