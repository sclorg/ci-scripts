#!/bin/bash

set -x

cd /root/ci-scripts/daily_tests
CUR_DATE=$(date +%Y-%m-%d)
id

#find "/var/ci-scripts" -ctime +30 -type d -exec rm-rf {} \;
echo "Daily nightly reports log files every 10 minutes..."
postfix start &
ls -la $SHARED_DIR/${CUR_DATE}
find "${SHARED_DIR}/${CUR_DATE}" -type f -name "tmt_*"
echo "--------------------"
python3 ./daily_nightly_tests_report.py
# Let's sleep for 10 minutes
