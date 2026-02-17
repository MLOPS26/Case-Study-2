#!/bin/bash
# sudo bash services/add-cron.sh

chmod +x /home/ubuntu/Case-Study-2/services/watchdog.sh

echo "* * * * * root /home/ubuntu/Case-Study-2/services/watchdog.sh" > /etc/cron.d/case-study-2-watchdog
chmod 644 /etc/cron.d/case-study-2-watchdog

echo "cron job installed"
