#!/bin/bash

set -x

[[ -z "$TARGET" ]] && { echo "You have to specify target to build SCL images. rhel9, rhel8, or fedora" && exit 1 ; }
[[ -z "$TESTS" ]] && { echo "You have to specify type of the test to run. test, test-pytest, test-openshift, test-openshift-pytest" && exit 1 ; }
SET_TEST=""
if [[ "${TESTS}" != "test-upstream" ]]; then
  [[ -z "$TEST_TYPE" ]] && { echo "You have to specify type of images S2I or NOS2I" && exit 1 ; }
  SET_TEST="$TEST_TYPE"
fi

# Local working directories
WORK_DIR="${HOME}/ci-scripts/"
LOCAL_LOGS_DIR="${HOME}/logs/"

# Shared directories between runs
DAILY_REPORTS_DIR="${SHARED_DIR}/daily_reports_dir"
TFT_PLAN="nightly-container-$TARGET"
DAILY_REPORTS_TESTS_DIR="${DAILY_REPORTS_DIR}/${TARGET}-${TESTS}"
DAILY_SCLORG_TESTS_DIR="${SHARED_DIR}/daily_scl_tests"

DIR="${WORK_DIR}/${TARGET}-${TESTS}-${SET_TEST}"
if [[ "$TESTS" == "test-upstream" ]]; then
  DIR="${WORK_DIR}/${TARGET}-${TESTS}"
fi
LOG_FILE="${LOCAL_LOGS_DIR}/${TARGET}-${TESTS}.log"


export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

function generate_passwd_file() {
    grep -v ^ci-scripts /etc/passwd > "$HOME/passwd"
    echo "ci-scripts:x:${USER_ID}:${GROUP_ID}:User for running ci-scripts:${HOME}:/bin/bash" >> "$HOME/passwd"
    export LD_PRELOAD=libnss_wrapper.so
    export NSS_WRAPPER_PASSWD=${HOME}/passwd
    export NSS_WRAPPER_GROUP=/etc/group
}

function move_logs_to_old() {
  echo "Moving logs to old directory"
  mv "${DAILY_REPORTS_DIR}/*" "${DAILY_REPORTS_DIR}_old/"
  echo "Logs moved to old directory"
}

function prepare_environment() {
  mkdir -p "${LOCAL_LOGS_DIR}"
  mkdir -p "${WORK_DIR}"
  mkdir -p "${DIR}"
  mkdir -p "${DAILY_REPORTS_TESTS_DIR}/plans/${TFT_PLAN}/data/results"

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
    COMPOSE="1MT-Fedora-${VERSION}"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
    TFT_PLAN="nightly-container-fedora"
  elif [[ "$TARGET" == "c9s" ]]; then
    COMPOSE="1MT-CentOS-Stream-9"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
    TFT_PLAN="nightly-container-centos-stream-9"
  elif [[ "$TARGET" == "c10s" ]]; then
    COMPOSE="1MT-CentOS-Stream-10"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
    TFT_PLAN="nightly-container-centos-stream-10"
  else
    echo "This target is not supported"
    exit 1
  fi
  COMPOSE=$(tmt -q run provision -h minute --list-images | grep $COMPOSE | head -n 1 | tr -d '[:space:]')
  export COMPOSE
}

function run_tests() {
  ENV_VARIABLES="-e DEBUG=yes -e SCRIPT=$SCRIPT -e OS=$TARGET -e TEST=$TESTS"
  if [[ "$TESTS" != "test-upstream" ]]; then
    ENV_VARIABLES="$ENV_VARIABLES -e SET_TEST=$SET_TEST"
  else
    ENV_VARIABLES="$ENV_VARIABLES -e CI=true"
  fi
  TMT_COMMAND="tmt run -v -v -d -d --all ${ENV_VARIABLES} --id ${DIR} plan --name $TFT_PLAN provision -v -v --how minute --auto-select-network --image ${COMPOSE}"
  echo "TMT command is: $TMT_COMMAND" | tee -a "${LOG_FILE}"
  touch "${RESULTS_TARGET_DIR}/tmt_running"
  set -o pipefail
  $TMT_COMMAND | tee -a "${LOG_FILE}"
  if [[ $? -ne 0 ]]; then
    echo "TMT command $TMT_COMMAND has failed."
    if [[ -f "${DAILY_REPORTS_TESTS_DIR}/tmt_success" ]]; then
      rm -f "${DAILY_REPORTS_TESTS_DIR}/tmt_success"
    fi
    touch "${DAILY_REPORTS_TESTS_DIR}/tmt_failed"
  else
    if [[ -f "${DAILY_REPORTS_TESTS_DIR}/tmt_failed" ]]; then
      echo "Previous test run has failed but this one has passed."
    else
      touch "${DAILY_REPORTS_TESTS_DIR}/tmt_success"
    fi
  fi
  ls -laR "${DIR}/plans/${TFT_PLAN}/data/" > "$DAILY_SCLORG_TESTS_DIR/all_files_${TARGET}_${TESTS}.txt"
  cp "${LOG_FILE}" "${DAILY_SCLORG_TESTS_DIR}/log_${TARGET}_${TESTS}.txt"
  if [[ -d "${DIR}/plans/${TFT_PLAN}/data" ]]; then
    cp -rv "${DIR}/plans/${TFT_PLAN}/data/results" "${DAILY_REPORTS_TESTS_DIR}/plans/${TFT_PLAN}/data/"
    cp -v "${DIR}/plans/${TFT_PLAN}/data/*.log" "${DAILY_REPORTS_TESTS_DIR}/plans/${TFT_PLAN}/data/"
  fi
  cp "${DIR}/log.txt" "${DAILY_REPORTS_TESTS_DIR}/"
  set +o pipefail
  rm -f "${DAILY_REPORTS_TESTS_DIR}/tmt_running"
}

if [[ "$TESTS" != "test" ]] && [[ "$TESTS" != "test-pytest" ]] && [[ "$TESTS" != "test-upstream" ]] && [[ "$TESTS" != "test-openshift-pytest" ]] && [[ "$TESTS" != "test-openshift-4" ]]; then
  echo "This test scenario is not enabled."
  exit 1
fi


CWD=$(pwd)
cd "$HOME" || { echo "Could not switch to $HOME"; exit 1; }
generate_passwd_file
# chown -R "${USER_ID}":0 $HOME/
# chown -R "${USER_ID}":0 $WORK_DIR/

prepare_environment
get_compose

# move_logs_to_old

date > "${LOG_FILE}"
curl --insecure -L https://url.corp.redhat.com/fmf-data > "/tmp/fmf_data"
source "/tmp/fmf_data"

env
echo "Switching to $WORK_DIR/$TMT_PLAN_DIR"
cd "$WORK_DIR/$TMT_PLAN_DIR" || { echo "Could not switch to $WORK_DIR/$TMT_PLAN_DIR"; exit 1; }
echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a "${LOG_FILE}"

run_tests

cd "$CWD" || exit 1
