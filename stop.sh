#!/bin/bash

WORKING_DIR="${PWD}/"
LUNGO_PID_FILE="${PWD}/gunicorn.pid"
NOTIFY_PID_FILE="${PWD}/notification_daemon.pid"

cd $WORKING_DIR

if [ ! -f $LUNGO_PID_FILE ];then
        echo "No pid file for Lungo, exiting"
else
        kill -15 `cat ${LUNGO_PID_FILE}`
        echo "Killed Lungo process from pid file"
fi

if [ ! -f $NOTIFY_PID_FILE ];then
        echo "No pid file for notification daemon, exiting"
else
        kill -15 `cat ${NOTIFY_PID_FILE}`
        echo "Killed Notification Daemon process from pid file"
fi
