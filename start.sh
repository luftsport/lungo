#!/bin/bash
echo "Error: This script is deprecated / not for use. Use 'startup.sh' instead" >&2
exit 1

INVENV=$(python -c 'import sys; print ("1" if hasattr(sys, "real_prefix") else "0")')

WORKING_DIR="${PWD}/"
GUNICORN="${PWD}/bin/gunicorn"
PYTHON="${PWD}/bin/python"
PID_PATH="/var/local/run/lungo/"
cd $WORKING_DIR

if [[ INVENV == 0 ]]
then
        source bin/activate
fi

umask 0022

# Membership api:
$GUNICORN --workers=5 --threads=20 --worker-class=meinheld.gmeinheld.MeinheldWorker -b localhost:9191 run:app --log-level=debug --log-file=unicorn.log --pid /var/local/run/lungo/lungo.pid --daemon

# Socket.io server, aiohttp:
$GUNICORN -w 1 --worker-class aiohttp.GunicornWebWorker notification_daemon:app -b localhost:7000 --pid /var/local/run/lungo/lungo_notification_daemon.pid --daemon

SERVICES=("notifications.service" "melwin.service" "sendgrid.service" "mailchimp.service")
printf "%-20s | %s\n" "SERVICE NAME" "STATUS"
echo "-------------------------------------"
for SERVICE in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$SERVICE"; then
        printf "%-20s | 🟢 Running\n" "$SERVICE"
    else
        printf "%-20s | 🔴 Down / Inactive\n" "$SERVICE"
    fi
done


if [[ INVENV == 0 ]]
then
        deactivate
fi

cd
