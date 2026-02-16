#!/bin/bash

set -x

cd /root/ci-scripts/daily_tests

while true; do
    find "/var/ci-scripts/daily_reports_dir/" -ctime +30 -type d
    find "/var/ci-scripts/daily_scl_tests/" -ctime +30 -type d
    #find "/var/ci-scripts" -ctime +30 -type d -exec rm-rf {} \;
    echo "Displaying log files every 10 minutes..."
    date
    find "${SHARED_DIR}/${CUR_DATE}" -type f -name "tmt_*"
    python3 ./show_logs.py
    # Let's sleep for 10 minutes
    sleep 600
done
