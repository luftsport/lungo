#!/bin/bash

INVENV=$(python -c 'import sys; print ("1" if hasattr(sys, "real_prefix") else "0")')

WORKING_DIR="${PWD}/"
GUNICORN="${PWD}/bin/gunicorn"
PYTHON="${PWD}/bin/python"

cd $WORKING_DIR

if [[ INVENV == 0 ]]
then
        source bin/acticate
fi

# Membership api:
$GUNICORN --workers=5 --threads=20 --worker-class=meinheld.gmeinheld.MeinheldWorker -b localhost:9191 run:app --log-level=debug --log-file=unicorn.log --pid gunicorn.pid --daemon

# Socket.io server, aiohttp:
$GUNICORN -w 1 --worker-class aiohttp.GunicornWebWorker notification_daemon:app -b localhost:7000 --pid notification_daemon.pid --daemon

# Start Melwin socket.io client
$PYTHON melwin_daemon.py 2>&1&

if [[ INVENV == 0 ]]
then
        deactivate
fi

cd