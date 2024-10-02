#!/bin/bash

set -x

LOGS_DIR="/home/fedora/logs"
DAILY_TEST_DIR="/var/tmp/daily_scl_tests"
WORK_DIR=$(mktemp -d -p "/var/tmp")
REPORTS_DIR="/var/tmp/daily_reports_dir"

if [ -d "${DAILY_TEST_DIR}" ]; then
  rm -rf "${DAILY_TEST_DIR}"
fi

if [ -d "${WORK_DIR}" ]; then
  rm -rf "${WORK_DIR}"
fi

if [ -d "${LOGS_DIR}" ]; then
  rm -rf "${LOGS_DIR}"
fi

if [ -d "${REPORTS_DIR}" ]; then
  rm -rf "${REPORTS_DIR}"
fi
