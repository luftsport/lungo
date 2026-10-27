#!/bin/bash

INVENV=$(python -c 'import sys; print ("1" if hasattr(sys, "real_prefix") else "0")')

WORKING_DIR="${PWD}/"
GUNICORN="${PWD}/bin/gunicorn"
PYTHON="${PWD}/bin/python"

cd $WORKING_DIR

if [[ INVENV == 0 ]]
then
        source bin/activate
fi

PID_FILE="/var/local/run/lungo/lungo.pid"
umask 0022
# Membership api:
#$GUNICORN --limit-request-line 4094 --worker-connections 1000 --limit-request-field_size 8192 --timeout 300  --workers=5 --threads=20 --worker-class=meinheld.gmeinheld.MeinheldWorker -b localhost:9191 run:app --log-level=debug --log-file=unicorn.log --pid gunicorn.pid --daemon
#$GUNICORN --limit-request-line 4094 --worker-connections 1000 --limit-request-field_size 8192 --timeout 300  --workers=5 --threads=20 --worker-class=gevent -b localhost:9191 run:app --log-level=debug --log-file=unicorn.log --pid gunicorn.pid --daemon
# gthread gevent
$GUNICORN \
  --worker-class=gthread \
  --workers=24 \
  --threads=8 \
  --timeout=30 \
  --keep-alive=65 \
  --max-requests=2000 \
  --max-requests-jitter=200 \
  --limit-request-line=4094 \
  --limit-request-field_size=8192 \
  --log-level=warning \
  --log-file=logs/unicorn.log \
  --pid="$PID_FILE" \
  -b localhost:9191 \
  --daemon \
  run:app

# Verify if needed services are running:
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