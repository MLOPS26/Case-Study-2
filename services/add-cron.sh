#!/bin/bash
# sudo bash services/add-cron.sh

chmod +x /home/group09/Case-Study-2/services/watchdog.sh

echo "* * * * * root /home/group09/Case-Study-2/services/watchdog.sh" > /etc/cron.d/case-study-2-watchdog
chmod 644 /etc/cron.d/case-study-2-watchdog

echo "cron job installed"
