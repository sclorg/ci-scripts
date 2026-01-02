#!/bin/bash

set -x

LOGS_DIR="$HOME/logs"
[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. rhel9, rhel8, or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-pytest, test-openshift, test-openshift-pytest, test-openshift-4" && exit 1 ; }
TESTS="$1"
shift
SET_TEST=""
if [[ "${TESTS}" != "test-upstream" ]]; then
  [[ -z "$1" ]] && { echo "You have to specify type of images S2I or NOS2I" && exit 1 ; }
  SET_TEST="$1"
fi

TMT_REPO="https://gitlab.cee.redhat.com/platform-eng-core-services/sclorg-tmt-plans"
DAILY_TEST_DIR="/var/tmp/daily_scl_tests"
RESULTS_DIR="/var/tmp/daily_reports_dir"
TMT_DIR="sclorg-tmt-plans"
API_KEY="API_KEY_PRIVATE"
TFT_PLAN="nightly-container-$TARGET"
if [[ "$TARGET" == "rhel8" ]]; then
  COMPOSE="1MT-RHEL-8.10.0-updates"
elif [[ "$TARGET" == "rhel9" ]]; then
  COMPOSE="1MT-RHEL-9.6.0-updates"
elif [[ "$TARGET" == "rhel10" ]]; then
  COMPOSE="1MT-RHEL-10.0"
elif [[ "$TARGET" == "fedora" ]]; then
  COMPOSE="1MT-Fedora-40"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-f"
elif [[ "$TARGET" == "c9s" ]]; then
  COMPOSE="1MT-CentOS-Stream-9"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-centos-stream-9"
elif [[ "$TARGET" == "c10s" ]]; then
  COMPOSE="1MT-CentOS-Stream-10"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-centos-stream-10"
elif [[ "$TARGET" == "c10s" ]]; then
  COMPOSE="1MT-CentOS-Stream-10"
  TMT_REPO="https://github.com/sclorg/sclorg-testing-farm"
  TMT_DIR="sclorg-testing-farm"
  TFT_PLAN="nightly-container-centos-stream-10"
else
  echo "This target is not supported"
  exit 1
fi

if [[ "$TESTS" != "test" ]] && [[ "$TESTS" != "test-upstream" ]] && [[ "$TESTS" != "test-openshift-pytest" ]] && [[ "$TESTS" != "test-openshift-4" ]]; then
  echo "This test scenario is not enabled."
  exit 1
fi

SCRIPT="daily_scl_tests"
WORK_DIR=$(mktemp -d -p "/var/tmp")
git clone "$TMT_REPO" "$WORK_DIR/$TMT_DIR"
CWD=$(pwd)
cd $HOME || { echo "Could not switch to $HOME"; exit 1; }
if [[ ! -d "${LOGS_DIR}" ]]; then
  mkdir -p "${LOGS_DIR}"
fi
if [[ ! -d "${RESULTS_DIR}" ]]; then
  mkdir -p "${RESULTS_DIR}"
fi
COMPOSE=$(tmt -q run provision -h minute --list-images | grep $COMPOSE | head -n 1 | tr -d '[:space:]')
DIR="${DAILY_TEST_DIR}/${TARGET}-${TESTS}-${SET_TEST}"
if [[ "$TESTS" == "test-upstream" ]]; then
  DIR="${DAILY_TEST_DIR}/${TARGET}-${TESTS}"
fi
mkdir -p "${RESULTS_DIR}/${TARGET}-${TESTS}/plans/${TFT_PLAN}/data/results"
mkdir -p "$DIR"
LOG="${LOGS_DIR}/$TARGET-$TESTS.log"

date > "${LOG}"
curl --insecure -L https://url.corp.redhat.com/fmf-data > /tmp/fmf_data
source /tmp/fmf_data

cd "$WORK_DIR/$TMT_DIR" || { echo "Could not switch to $WORK_DIR/$TMT_DIR"; exit 1; }
echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a "${LOG}"
RESULTS_TARGET_DIR="${RESULTS_DIR}/${TARGET}-${TESTS}"
touch "${RESULTS_TARGET_DIR}/tmt_running"
if [[ "$TESTS" == "test-upstream" ]]; then
  TMT_COMMAND="tmt run -v -v -d -d --all -e SCRIPT=$SCRIPT -e OS=$TARGET -e TEST=$TESTS --id ${DIR} plan --name $TFT_PLAN provision --how minute --auto-select-network --image ${COMPOSE}"
else
  TMT_COMMAND="tmt run -v -v -d -d --all -e SCRIPT=$SCRIPT -e OS=$TARGET -e SET_TEST=$SET_TEST -e TEST=$TESTS --id ${DIR} plan --name $TFT_PLAN provision --how minute --auto-select-network --image ${COMPOSE}"
fi
echo "TMT command is: $TMT_COMMAND" | tee -a "${LOG}"
set -o pipefail
$TMT_COMMAND | tee -a "${LOG}"
if [[ $? -ne 0 ]]; then
  echo "TMT command $TMT_COMMAND has failed."
  if [[ -f "${RESULTS_TARGET_DIR}/tmt_success" ]]; then
    rm -f "${RESULTS_TARGET_DIR}/tmt_success"
  fi
  touch "${RESULTS_TARGET_DIR}/tmt_failed"
else
  if [[ -f "${RESULTS_TARGET_DIR}/tmt_failed" ]]; then
    echo "Previous test run has failed but this one has passed."
  else
    touch "${RESULTS_TARGET_DIR}/tmt_success"
  fi
fi
if [[ -d "${DIR}/plans/${TFT_PLAN}/data" ]]; then
  cp -rv "${DIR}/plans/${TFT_PLAN}/data/results" "${RESULTS_TARGET_DIR}/plans/${TFT_PLAN}/data/"
  cp -v "${DIR}/plans/${TFT_PLAN}/data/*.log" "${RESULTS_TARGET_DIR}/plans/${TFT_PLAN}/data/"
fi
cp "${DIR}/log.txt" "${RESULTS_TARGET_DIR}/"
set +o pipefail
rm -f "${RESULTS_TARGET_DIR}/tmt_running"
cd "$CWD" || exit 1
rm -rf "$WORK_DIR"
