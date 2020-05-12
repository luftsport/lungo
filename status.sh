#!/bin/bash

WORKING_DIR="${PWD}/"
echo "DIR IS '$WORKING_DIR'"

cd $WORKING_DIR

if [ -f gunicorn.pid ];then
        echo "LUNGO is running"
else
        echo "!!LUNGO is NOT running!"
fi

if [ -f notification_daemon.pid ];then
        echo "NOTIFICATION is running"
else
        echo "!!NOTIFICATION is NOT running!"
fi
