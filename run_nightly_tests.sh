#!/bin/bash

set -x

LOGS_DIR="/home/fedora/logs"
[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. c9s, c8s, rhel8, centos7, rhel7 or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-openshift, test-openshift-4" && exit 1 ; }
TESTS="$1"

TMT_REPO="https://gitlab.cee.redhat.com/platform-eng-core-services/sclorg-tmt-plans"
DAILY_TEST_DIR="/var/tmp/daily_scl_tests"
TMT_DIR="sclorg-tmt-plans"
API_KEY="API_KEY_PRIVATE"
TFT_PLAN="nightly-container-$TARGET"
if [[ "$TARGET" == "rhel8" ]]; then
  COMPOSE="1MT-RHEL-8.8.0-updates"
elif [[ "$TARGET" == "rhel7" ]]; then
  COMPOSE="1MT-RHEL-7.9-updates"
elif [[ "$TARGET" == "rhel9" ]]; then
  COMPOSE="1MT-RHEL-9.2.0-updates"
elif [[ "$TARGET" == "centos7" ]]; then
  COMPOSE="1MT-CentOS-7"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-centos-7"
elif [[ "$TARGET" == "fedora" ]]; then
  COMPOSE="1MT-Fedora-37"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-f"
elif [[ "$TARGET" == "c9s" ]]; then
  COMPOSE="1MT-CentOS-Stream-9"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-centos-stream-9"
elif [[ "$TARGET" == "c8s" ]]; then
  COMPOSE="1MT-CentOS-Stream-8"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-centos-stream-8"
else
  echo "This target is not supported"
  exit 1
fi

if [[ "$TESTS" != "test" ]] && [[ "$TESTS" != "test-openshift" ]] && [[ "$TESTS" != "test-openshift-4" ]]; then
  echo "This test scenario is not enabled."
  exit 1
fi

WORK_DIR=$(mktemp -d -p "/var/tmp")
git clone "$TMT_REPO" "$WORK_DIR/$TMT_DIR"
CWD=$(pwd)
cd /home/fedora || { echo "Could not switch to /home/fedora"; exit 1; }
if [[ ! -d "${LOGS_DIR}" ]]; then
  mkdir -p "${LOGS_DIR}"
fi
COMPOSE=$(tmt -q run provision -h minute --list-images | grep $COMPOSE | head -n 1 | tr -d '[:space:]')
echo "COMPOSE is $COMPOSE" | tee -a ${LOG}
if [ -d "${DAILY_TEST_DIR}/${TARGET}-$TESTS" ]; then
  rm -rf "${DAILY_TEST_DIR}/${TARGET}-$TESTS"
fi
mkdir -p "${DAILY_TEST_DIR}/${TARGET}-$TESTS"
LOG="${LOGS_DIR}/$TARGET-$TESTS.log"
date > "${LOG}"
curl -L https://url.corp.redhat.com/fmf-data > /tmp/fmf_data
source /tmp/fmf_data

cd "$WORK_DIR/$TMT_DIR" || { echo "Could not switch to $WORK_DIR/$TMT_DIR"; exit 1; }
echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a "${LOG}"
touch "${DAILY_TEST_DIR}/$TARGET-$TESTS/tmt_running"
TMT_COMMAND="tmt run -v -v -d -d --all -e OS=$TARGET -e TEST=$TESTS --id ${DAILY_TEST_DIR}/$TARGET-$TESTS plan --name $TFT_PLAN provision --how minute --auto-select-network --image ${COMPOSE}"
echo "TMT command is: $TMT_COMMAND" | tee -a "${LOG}"
out=$(TMT_COMMAND); exitcode=$?; echo "$out" >> "${LOG}"
if [[ "$exitcode" != "0" ]]; then
  echo "TMT command $TMT_COMMAND has failed."
  touch "${DAILY_TEST_DIR}/$TARGET-$TESTS/tmt_failed"
else
  touch "${DAILY_TEST_DIR}/$TARGET-$TESTS/tmt_success"
fi
rm -f "${DAILY_TEST_DIR}/$TARGET-$TESTS/tmt_running"
cd "$CWD" || exit 1
rm -rf "$WORK_DIR"
