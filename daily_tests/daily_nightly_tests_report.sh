#!/bin/bash

set -x

cd /root/ci-scripts/daily_tests
CUR_DATE=$(date +%Y-%m-%d)

echo "Bash arguments: $@"
# Let's sleep for 10 minutes
env
find "/var/ci-scripts/daily_reports_dir/${CUR_DATE}" -type f -name "tmt_*"
echo "--------------------"
if [ -n "$1" ]; then
    python3 ./daily_nightly_tests_report.py "$1"
else
    python3 ./daily_nightly_tests_report.py
fi
