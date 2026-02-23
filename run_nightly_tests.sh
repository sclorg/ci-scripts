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

cd "/root/ci-scripts/"

# Local working directories
CUR_DATE=$(date +%Y-%m-%d)
WORK_DIR="${HOME}/ci-scripts"
LOCAL_LOGS_DIR="${HOME}/logs"

# Shared directories between runs
DAILY_REPORTS_DIR="${SHARED_DIR}/daily_reports_dir/${CUR_DATE}"
TFT_PLAN="nightly/nightly-$TARGET"
DAILY_REPORTS_TESTS_DIR="${DAILY_REPORTS_DIR}/${TARGET}-${TESTS}"
DAILY_SCLORG_TESTS_DIR="${SHARED_DIR}/daily_scl_tests/${CUR_DATE}/${TARGET}-${TESTS}"

DIR="${WORK_DIR}/${CUR_DATE}/${TARGET}-${TESTS}"
LOG_FILE="${LOCAL_LOGS_DIR}/${TARGET}-${TESTS}.log"


export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
API_KEY="API_KEY_PRIVATE"
# function generate_passwd_file() {
#     grep -v ^ci-scripts /etc/passwd > "$HOME/passwd"
#     echo "ci-scripts:x:${USER_ID}:${GROUP_ID}:User for running ci-scripts:${HOME}:/bin/bash" >> "$HOME/passwd"
#     export LD_PRELOAD=libnss_wrapper.so
#     export NSS_WRAPPER_PASSWD=${HOME}/passwd
#     export NSS_WRAPPER_GROUP=/etc/group
# }
BRANCH="master"
function prepare_environment() {
  mkdir -p "${LOCAL_LOGS_DIR}"
  mkdir -p "${WORK_DIR}"
  mkdir -p "${DIR}"
  mkdir -p "${DAILY_REPORTS_TESTS_DIR}/results"
  mkdir -p "${DAILY_SCLORG_TESTS_DIR}"

}

function get_compose() {
  if [[ "$TARGET" == "rhel8" ]]; then
    # COMPOSE="1MT-RHEL-8.10.0-updates"
    COMPOSE="RHEL-8.10.0-Nightly"
    TMT_PLAN_URL="$DOWNSTREAM_TMT_REPO"
  elif [[ "$TARGET" == "rhel9" ]]; then
    # COMPOSE="1MT-RHEL-9.6.0-updates"
    COMPOSE="RHEL-9.6.0-Nightly"
    TMT_PLAN_URL="$DOWNSTREAM_TMT_REPO"
  elif [[ "$TARGET" == "rhel10" ]]; then
    # COMPOSE="1MT-RHEL-10.0"
    COMPOSE="RHEL-10-Nightly"
    TMT_PLAN_URL="$DOWNSTREAM_TMT_REPO"
  elif [[ "$TARGET" == "fedora" ]]; then
    # COMPOSE="1MT-Fedora-${VERSION}"
    COMPOSE="Fedora-latest"
    TMT_PLAN_URL="$UPSTREAM_TMT_REPO"
    TFT_PLAN="nightly/nightly-fedora"
    API_KEY="API_KEY_PUBLIC"
    BRANCH="main"
  elif [[ "$TARGET" == "c9s" ]]; then
    # COMPOSE="1MT-CentOS-Stream-9"
    COMPOSE="CentOS-Stream-9"
    TMT_PLAN_URL="$UPSTREAM_TMT_REPO"
    TFT_PLAN="nightly/nightly-c9s"
    API_KEY="API_KEY_PUBLIC"
    BRANCH="main"
  elif [[ "$TARGET" == "c10s" ]]; then
    # COMPOSE="1MT-CentOS-Stream-10"
    COMPOSE="CentOS-Stream-10"
    TMT_PLAN_URL="$UPSTREAM_TMT_REPO"
    TFT_PLAN="nightly/nightly-c10s"
    API_KEY="API_KEY_PUBLIC"
    BRANCH="main"
  else
    echo "This target is not supported"
    exit 1
  fi
  # COMPOSE=$(tmt -q run provision -h minute --list-images | grep $COMPOSE | head -n 1 | tr -d '[:space:]')
  # export COMPOSE
  # export TMT_PLAN
}

function run_tests() {
  env
  touch "${DAILY_SCLORG_TESTS_DIR}/tmt_running"
  cat "$HOME/fmf_data" | grep "$API_KEY" | cut -d '=' -f2
  export TESTING_FARM_API_TOKEN=$(cat "$HOME/fmf_data" | grep "$API_KEY" | cut -d '=' -f2)
  TESTING_FARM_CMD="testing-farm request --compose ${COMPOSE} -e OS=${TARGET} -e TEST=${TESTS} --git-url ${TMT_PLAN_URL} --git-ref ${BRANCH} --plan ${TFT_PLAN} --duration 240"
  $TESTING_FARM_CMD | tee -a "${LOG_FILE}"
  ret_code=$?
  rm -f "${DAILY_SCLORG_TESTS_DIR}/tmt_running"
  # Let's sleep 5 minutes to let the testing farm to start the tests and generate some logs
  sleep 300
  if [[ $ret_code -ne 0 ]]; then
    echo "Testing Farm command $TESTING_FARM_CMD has failed."
    touch "${DAILY_REPORTS_TESTS_DIR}/tmt_failed"
  fi
  grep "tests passed" "${LOG_FILE}"
  if grep "tests passed" "${LOG_FILE}"; then
    touch "${DAILY_REPORTS_TESTS_DIR}/tmt_success"
  else
    touch "${DAILY_REPORTS_TESTS_DIR}/tmt_failed"
  fi
  cp "${LOG_FILE}" "${DAILY_REPORTS_TESTS_DIR}/testing_farm_${TARGET}_${TESTS}.txt"
  python3 /root/ci-scripts/daily_tests/download_logs.py "${LOG_FILE}" "${TARGET}" "${TESTS}"
}

if [[ "$TESTS" != "test" ]] && [[ "$TESTS" != "test-pytest" ]] && [[ "$TESTS" != "test-upstream" ]] && [[ "$TESTS" != "test-openshift-pytest" ]] && [[ "$TESTS" != "test-openshift-4" ]]; then
  echo "This test scenario is not enabled."
  exit 1
fi


CWD=$(pwd)
cd "$HOME" || { echo "Could not switch to $HOME"; exit 1; }
#generate_passwd_file

prepare_environment
get_compose


date > "${LOG_FILE}"

env
echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a "${LOG_FILE}"

run_tests

cd "$CWD" || exit 1
