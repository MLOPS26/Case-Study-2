#!/bin/bash
# sudo bash services/add-cron-backend.sh

chmod +x /home/group09/Case-Study-2/services/watchdog-backend.sh

echo "* * * * * root /home/group09/Case-Study-2/services/watchdog-backend.sh" > /etc/cron.d/case-study-2-watchdog
chmod 644 /etc/cron.d/case-study-2-watchdog

echo "cron job installed"
