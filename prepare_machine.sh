#!/bin/bash

set -x

LOGS_DIR="$HOME/logs"
DAILY_TEST_DIR="/var/tmp/daily_scl_tests"
WORK_DIR=$(mktemp -d -p "/var/tmp")
REPORTS_DIR="/var/tmp/daily_reports_dir"

if [ -d "${DAILY_TEST_DIR}" ]; then
  rm -rf "${DAILY_TEST_DIR}"
fi
mkdir -p "${DAILY_TEST_DIR}"

if [ -d "${WORK_DIR}" ]; then
  rm -rf "${WORK_DIR}"
fi
mkdir -p "${WORK_DIR}"

if [ -d "${LOGS_DIR}" ]; then
  rm -rf "${LOGS_DIR}"
fi
mkdir -p "${LOGS_DIR}"

if [ -d "${REPORTS_DIR}" ]; then
  rm -rf "${REPORTS_DIR}"
fi
mkdir -p "${REPORTS_DIR}"
