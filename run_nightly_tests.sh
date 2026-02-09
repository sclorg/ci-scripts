#!/bin/bash

set -x

if [[ -n "$TARGET" ]]; then
  echo "Target is set to $TARGET"
else
  echo "TARGET variable is not set. Please set it to rhel9, rhel8, rhel10, fedora, c9s or c10s."
  exit 1
fi
if [[ -n "$TESTS" ]]; then
  echo "Test is set to $TESTS"
else
  echo "TESTS variable is not set. Please set it to test, test-pytest, test-openshift, or test-openshift-pytest."
  exit 1
fi

# Local working directories
CUR_DATE=$(date +%Y-%m-%d)
WORK_DIR="${HOME}/ci-scripts/"
LOCAL_LOGS_DIR="${HOME}/logs/"

# Shared directories between runs
DAILY_REPORTS_DIR="${SHARED_DIR}/daily_reports_dir/${CUR_DATE}"
TFT_PLAN="nightly/nightly-$TARGET"
DAILY_REPORTS_TESTS_DIR="${DAILY_REPORTS_DIR}/${TARGET}-${TESTS}"
DAILY_SCLORG_TESTS_DIR="${SHARED_DIR}/daily_scl_tests/${CUR_DATE}/${TARGET}-${TESTS}"

DIR="${WORK_DIR}/${CUR_DATE}/${TARGET}-${TESTS}"
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
    TFT_PLAN="nightly/nightly-fedora"
  elif [[ "$TARGET" == "c9s" ]]; then
    COMPOSE="1MT-CentOS-Stream-9"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
    TFT_PLAN="nightly/nightly-c9s"
  elif [[ "$TARGET" == "c10s" ]]; then
    COMPOSE="1MT-CentOS-Stream-10"
    TMT_PLAN_DIR="$UPSTREAM_TMT_DIR"
    TFT_PLAN="nightly/nightly-c10s"
  else
    echo "This target is not supported"
    exit 1
  fi
  COMPOSE=$(tmt -q run provision -h minute --list-images | grep $COMPOSE | head -n 1 | tr -d '[:space:]')
  export COMPOSE
}

function run_tests() {
  # -e CI=true is set for NodeJS Upstream tests
  ENV_VARIABLES="-e DEBUG=yes -e OS=$TARGET -e TEST=$TESTS -e CI=true"
  TMT_COMMAND="tmt run -v -v -d -d --all ${ENV_VARIABLES} --id ${DIR} plan --name $TFT_PLAN provision -v -v --how minute --auto-select-network --image ${COMPOSE}"
  echo "TMT command is: $TMT_COMMAND" | tee -a "${LOG_FILE}"
  touch "${DAILY_SCLORG_TESTS_DIR}/tmt_running"
  set -o pipefail
  $TMT_COMMAND | tee -a "${LOG_FILE}"
  ret_code=$?
  set +o pipefail
  rm -f "${DAILY_SCLORG_TESTS_DIR}/tmt_running"
  if [[ $ret_code -ne 0 ]]; then
    echo "TMT command $TMT_COMMAND has failed."
    touch "${DAILY_REPORTS_TESTS_DIR}/tmt_failed"
  else
    touch "${DAILY_REPORTS_TESTS_DIR}/tmt_success"
  fi
  cp "${LOG_FILE}" "${DAILY_SCLORG_TESTS_DIR}/log_${TARGET}_${TESTS}.txt"
  if [[ -d "${DIR}/plans/${TFT_PLAN}/data" ]]; then
    ls -laR "${DIR}/plans/${TFT_PLAN}/data/" > "$DAILY_SCLORG_TESTS_DIR/all_files_${TARGET}_${TESTS}.txt"
    ls -la "${DIR}/plans/${TFT_PLAN}/data/results/"
    cp -rv "${DIR}/plans/${TFT_PLAN}/data/results" "${DAILY_REPORTS_TESTS_DIR}/plans/${TFT_PLAN}/data/"
    cp -v "${DIR}/plans/${TFT_PLAN}/data/*.log" "${DAILY_REPORTS_TESTS_DIR}/plans/${TFT_PLAN}/data/"
  fi
  cp "${DIR}/log.txt" "${DAILY_REPORTS_TESTS_DIR}/"
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

move_logs_to_old

prepare_environment
get_compose


date > "${LOG_FILE}"
curl --insecure -L https://url.corp.redhat.com/fmf-data > "/tmp/fmf_data"
source "/tmp/fmf_data"

env
echo "Switching to $WORK_DIR/$TMT_PLAN_DIR"
cd "$WORK_DIR/$TMT_PLAN_DIR" || { echo "Could not switch to $WORK_DIR/$TMT_PLAN_DIR"; exit 1; }
echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a "${LOG_FILE}"

run_tests

cd "$CWD" || exit 1
