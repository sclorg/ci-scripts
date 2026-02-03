#!/bin/bash

set -x

while true; do
    echo "Displaying log files every 10 minutes..."
    python3 /root/ci-scripts/show_logs.py
    # Let's sleep for 10 minutes
    sleep 600
done
