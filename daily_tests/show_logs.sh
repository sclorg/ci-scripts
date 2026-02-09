#!/bin/bash

set -x

cd /root/ci-scripts/daily_tests

while true; do
    echo "Displaying log files every 10 minutes..."
    date
    python3 ./show_logs.py
    # Let's sleep for 10 minutes
    sleep 600
done
