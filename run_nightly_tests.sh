#!/bin/bash

[[ -z "$TARGET" ]] && { echo "You have to specify target to build SCL images. rhel9, rhel8, or fedora" && exit 1 ; }
[[ -z "$TESTS" ]] && { echo "You have to specify type of the test to run. test, test-pytest, test-openshift, test-openshift-pytest" && exit 1 ; }
SET_TEST=""
if [[ "${TESTS}" != "test-upstream" ]]; then
  [[ -z "$TEST_TYPE" ]] && { echo "You have to specify type of images S2I or NOS2I" && exit 1 ; }
  SET_TEST="$TEST_TYPE"
fi

LOGS_DIR="${WORK_DIR}/daily_tests_logs/"
LOGS_DIR_OLD="${LOGS_DIR}/old"
DAILY_TEST_DIR="${WORK_DIR}/daily_scl_tests"
RESULTS_DIR="${WORK_DIR}/daily_reports_dir"
RESULTS_DIR_OLD="${RESULTS_DIR}/old"
SCRIPT="daily_scl_tests"
TFT_PLAN="nightly-container-$TARGET"
DIR="${DAILY_TEST_DIR}/${TARGET}-${TESTS}-${SET_TEST}"
RESULTS_TARGET_DIR="${RESULTS_DIR}/${TARGET}-${TESTS}"
if [[ "$TESTS" == "test-upstream" ]]; then
  DIR="${DAILY_TEST_DIR}/${TARGET}-${TESTS}"
fi
LOG_FILE="${LOGS_DIR}/${TARGET}-${TESTS}.log"

function move_logs_to_old() {
  echo "Moving logs to old directory"
  if [[ -d "${LOGS_DIR_OLD}" ]]; then
    rm -rf "${LOGS_DIR_OLD}/*"
  fi
  if [[ -d "${RESULTS_DIR_OLD}" ]]; then
    rm -rf "${RESULTS_DIR_OLD}/*"
  fi
  mv "${LOG_FILE}/*" "${LOGS_DIR_OLD}/"
  mv "${RESULTS_TARGET_DIR}/*" "${RESULTS_DIR_OLD}/"
  echo "Logs moved to old directory"
}

function prepare_environment() {
  if [[ ! -d "${LOGS_DIR}" ]]; then
    mkdir -p "${LOGS_DIR}"
  fi
  if [[ ! -d "${RESULTS_DIR}" ]]; then
    mkdir -p "${RESULTS_DIR}"
  fi
  if [[ ! -d "${LOGS_DIR_OLD}" ]]; then
    mkdir -p "${LOGS_DIR_OLD}"
  fi
  if [[ ! -d "${RESULTS_DIR_OLD}" ]]; then
    mkdir -p "${RESULTS_DIR_OLD}"
  fi
  mkdir -p "${RESULTS_TARGET_DIR}/plans/${TFT_PLAN}/data/results"
  mkdir -p "$DIR"
}

function get_compose() {
  if [[ "$TARGET" == "rhel8" ]]; then
    COMPOSE="1MT-RHEL-8.10.0-updates"
    TMT_PLAN_DIR="$DOWNSTREAM_TMT_DIR"
  elif [[ "$TARGET" == "rhel9" ]]; then
    COMPOSE="1MT-RHEL-9.6.0-updates"
    TMT_PLAN_DIR="$DOWNSTREAM_TMT_DIR"
  elif [[ "$TARGET" == "rhel10" ]]; then
    COMPOSE="1MT-RHEL-10.0"
    TMT_PLAN_DIR="$DOWNSTREAM_TMT_DIR"
  elif [[ "$TARGET" == "fedora" ]]; then
    COMPOSE="1MT-Fedora-40"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
  elif [[ "$TARGET" == "c9s" ]]; then
    COMPOSE="1MT-CentOS-Stream-9"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
  elif [[ "$TARGET" == "c10s" ]]; then
    COMPOSE="1MT-CentOS-Stream-10"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
  else
    echo "This target is not supported"
    exit 1
  fi
  COMPOSE=$(tmt -q run provision -h minute --list-images | grep $COMPOSE | head -n 1 | tr -d '[:space:]')
  export COMPOSE
}

function run_tests() {
  ENV_VARIABLES="-e DEBUG=yes -e SCRIPT=$SCRIPT -e OS=$TARGET"
  if [[ "$TESTS" == "test-upstream" ]]; then
    ENV_VARIABLES="$ENV_VARIABLES -e TEST=$TESTS"
  else
    ENV_VARIABLES="$ENV_VARIABLES -e SET_TEST=$SET_TEST"
  fi
  TMT_COMMAND="tmt run -v -v -d -d --all ${ENV_VARIABLES} --id ${DIR} plan --name $TFT_PLAN provision --how minute --auto-select-network --image ${COMPOSE}"
  echo "TMT command is: $TMT_COMMAND" | tee -a "${LOG_FILE}"
  touch "${RESULTS_TARGET_DIR}/tmt_running"
  set -o pipefail
  $TMT_COMMAND | tee -a "${LOG_FILE}"
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
}




if [[ "$TESTS" != "test" ]] && [[ "$TESTS" != "test-pytest" ]] && [[ "$TESTS" != "test-upstream" ]] && [[ "$TESTS" != "test-openshift-pytest" ]] && [[ "$TESTS" != "test-openshift-4" ]]; then
  echo "This test scenario is not enabled."
  exit 1
fi


CWD=$(pwd)
cd "$HOME" || { echo "Could not switch to $HOME"; exit 1; }
prepare_environment
get_compose

move_logs_to_old

date > "${LOG_FILE}"
curl --insecure -L https://url.corp.redhat.com/fmf-data > "/tmp/fmf_data"
source "/tmp/fmf_data"

env
echo "Switching to $WORK_DIR/$TMT_PLAN_DIR"
cd "$WORK_DIR/$TMT_PLAN_DIR" || { echo "Could not switch to $WORK_DIR/$TMT_PLAN_DIR"; exit 1; }
echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a "${LOG_FILE}"

run_tests

cd "$CWD" || exit 1
rm -rf "$WORK_DIR"
