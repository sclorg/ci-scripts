#!/bin/bash

set -x

LOGS_DIR="/home/fedora/logs"

TARGET="rhel9"
TMT_REPO="https://gitlab.cee.redhat.com/platform-eng-core-services/sclorg-tmt-plans"
DAILY_TEST_DIR="/var/tmp/daily_scl_tests"
RESULTS_DIR="/var/tmp/daily_reports_dir"
TMT_DIR="sclorg-tmt-plans"
API_KEY="API_KEY_PRIVATE"
TFT_PLAN="nightly-container-rhel9"
COMPOSE="1MT-RHEL-9.4.0-updates"
TESTS="helm-charts"
SCRIPT="daily_helm_charts"

WORK_DIR=$(mktemp -d -p "/var/tmp")
git clone "$TMT_REPO" "$WORK_DIR/$TMT_DIR"
CWD=$(pwd)
cd /home/fedora || { echo "Could not switch to /home/fedora"; exit 1; }
if [[ ! -d "${LOGS_DIR}" ]]; then
  mkdir -p "${LOGS_DIR}"
fi
if [[ ! -d "${RESULTS_DIR}" ]]; then
  mkdir -p "${RESULTS_DIR}"
fi
COMPOSE=$(tmt -q run provision -h minute --list-images | grep $COMPOSE | head -n 1 | tr -d '[:space:]')
DIR="${DAILY_TEST_DIR}/${TARGET}-${TESTS}"
if [ -d "${DAILY_TEST_DIR}/${TARGET}-$TESTS" ]; then
  rm -rf "${DAILY_TEST_DIR}/${TARGET}-$TESTS"
fi
mkdir -p "${RESULTS_DIR}/${TARGET}-${TESTS}/plans/${TFT_PLAN}/data/results"
mkdir -p "${DAILY_TEST_DIR}/${TARGET}-$TESTS"
LOG="${LOGS_DIR}/$TARGET-$TESTS.log"
date > "${LOG}"
curl --insecure -L https://url.corp.redhat.com/fmf-data > /tmp/fmf_data
source /tmp/fmf_data

cd "$WORK_DIR/$TMT_DIR" || { echo "Could not switch to $WORK_DIR/$TMT_DIR"; exit 1; }
echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a "${LOG}"
touch "${RESULTS_DIR}/${TARGET}-${TESTS}/tmt_running"
TMT_COMMAND="tmt run -v -v -d -d --all -e SCRIPT=$SCRIPT -e OS=$TARGET -e TEST=$TESTS --id ${DAILY_TEST_DIR}/$TARGET-$TESTS plan --name $TFT_PLAN provision --how minute --auto-select-network --image ${COMPOSE}"
echo "TMT command is: $TMT_COMMAND" | tee -a "${LOG}"
set -o pipefail
$TMT_COMMAND | tee -a "${LOG}"
if [[ $? -ne 0 ]]; then
  echo "TMT command $TMT_COMMAND has failed."
  touch "${RESULTS_DIR}/${TARGET}-${TESTS}/tmt_failed"
else
  touch "${RESULTS_DIR}/${TARGET}-${TESTS}/tmt_success"
fi
if [[ -d "${DIR}/plans/${TFT_PLAN}/data" ]]; then
  cp -rv "${DIR}/plans/${TFT_PLAN}/data/results" "${RESULTS_DIR}/${TARGET}-${TESTS}/plans/${TFT_PLAN}/data/"
  cp -v "${DIR}/plans/${TFT_PLAN}/data/*.log" "${RESULTS_DIR}/${TARGET}-${TESTS}/plans/${TFT_PLAN}/data/"
fi
cp "${DIR}/log.txt" "${RESULTS_DIR}/${TARGET}-${TESTS}/"
set +o pipefail
rm -f "${RESULTS_DIR}/${TARGET}-${TESTS}/tmt_running"
cd "$CWD" || exit 1
rm -rf "$WORK_DIR"
