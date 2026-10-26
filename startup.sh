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

# Socket.io server, aiohttp:
# $GUNICORN -w 1 --worker-class aiohttp.GunicornWebWorker notification_daemon:app -b localhost:7000 --pid notification_daemon.pid --daemon

# Start Melwin socket.io client
#$PYTHON melwin_daemon.py 2>&1&
#nohup melwin_daemon.py > logs/melwin_daemon.log &
#killall melwin_daemon.py
#$PYTHON melwin_daemon.py > logs/melwin_daemon.log 2>&1 &
#$PYTHON mailchimp_daemon.py 2>&1&
#nohup mailchimp_daemon.py > logs/mailchimp_daemon.log &
#killall mailchimp_daemon.py
#$PYTHON mailchimp_daemon.py > logs/mailchimp_daemon.log 2>&1 &
# /dev/null 2>&1
#killall sendgrid_daemon.py
#$PYTHON sendgrid_daemon.py > logs/sendgrid_daemon.log 2>&1 &

if [[ INVENV == 0 ]]
then
        deactivate
fi

cd