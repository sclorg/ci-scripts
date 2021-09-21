#!/bin/bash

SCL_CONTAINERS="s2i-base-container \
s2i-nodejs-container \
s2i-php-container \
s2i-perl-container \
s2i-ruby-container \
s2i-python-container \
postgresql-container \
varnish-container \
nginx-container \
httpd-container \
mariadb-container \
redis-container \
mysql-container \
mongodb-container
"


[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. centos7, rhel7 or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-openshift, test-openshift-4" && exit 1 ; }
TESTS="$1"

TMP_DIR="/tmp/daily_scl_tests-$TARGET"
RESULT_DIR="${TMP_DIR}/results/"
REQ_ID=""
if [[ -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR:?}/"
fi
if [[ x"$TARGET" == "xrhel8" ]]; then
  COMPOSE="RHEL-8.3.1-Released"
  OS_SYSTEM="rhel8"
else
  COMPOSE="RHEL-7.9-Released"
  OS_SYSTEM="rhel7"
fi

mkdir -p "${RESULT_DIR}"
curl -L https://url.corp.redhat.com/fmf-data > /tmp/fmf_data
source /tmp/fmf_data

function clone_repo() {
    local repo_name=$1; shift
    # Sometimes clonning failed with an error
    # The requested URL returned error: 500. Save it into log for info
    git clone "https://github.com/sclorg/${repo_name}.git" || \
        { echo "Repository ${repo_name} was not clonned." > ${RESULT_DIR}/${repo_name}.log; return 1 ; }
    cd "${repo_name}" || { echo "Repository ${repo_name} does not exist. Skipping." && return 1 ; }
    git submodule update --init
    git submodule update --remote
}

function check_state() {
  echo "Check state for $REQ_ID"
  CMD="$TF_ENDPOINT/requests/$REQ_ID"
  curl $CMD > job.json
  state=$(jq -r .state job.json)
  # Wait till job is not finished. As soon as state is complete or failure then go to the finish action
  while [ "$state" == "running" ] || [ "$state" == "new" ] || [ "$state" == "pending" ] || [ "$state" == "queued" ]; do
    # Wait 30s. We do not need to query Testing Farm each second
    sleep 30
    curl $CMD > job.json
    state=$(jq -r .state job.json)
  cat job.json
  done
}

function final_report() {
  curl $TF_ENDPOINT/requests/$REQ_ID > job.json
  cat job.json
  state=$(jq -r .state job.json)
  result=$(jq -r .result.overall job.json)
  new_state="success"
  infra_error=" "
  echo "State is $state and result is: $result"
  if [ "$state" == "complete" ]; then
    if [ "$result" != "passed" ]; then
      new_state="failure"
    fi
  else
    # Mark job in case of infrastructure issues. Report to Testing Farm team
    infra_error=" - Infra problems"
    new_state="failure"
  fi
  if [[ x"$new_state" == "failure" ]]; then
    curl $TF_LOG/$REQ_ID/pipeline.log > "${RESULT_DIR}/${repo}.log"
  fi
  echo "New State: $new_state"
  echo "Infra state: $infra_error"
}

function schedule_testing_farm_request() {
  cat << EOF > request.json
    {
      "api_key": "$API_KEY",
      "test": {"fmf": {
      "url": "https://gitlab.cee.redhat.com/platform-eng-core-services/sclorg-tmt-plans",
      "ref": "master",
      "name": "nightly-$OS_SYSTEM"
      }},
      "environments": [{
      "arch": "x86_64",
      "os": {"compose": "$COMPOSE"},
      "variables": {
        "REPO_URL": "https://github.com/sclorg/$repo",
        "REPO_NAME": "$repo",
        "TEST_SUITE": "$TESTS",
        "OS": "$TARGET"
      }}]
    }
EOF
  cat request.json
  curl $TF_ENDPOINT/requests --data @request.json --header "Content-Type: application/json" --output response.json
  cat response.json
  REQ_ID=$(jq -r .id response.json)
  echo "$REQ_ID"
}

function iterate_over_all_containers() {
    for repo in ${SCL_CONTAINERS}; do
      REQ_ID=""
      cd ${TMP_DIR} || exit
      local log_name="${TMP_DIR}/${repo}.log"
      clone_repo "${repo}"
      if [ $? -ne 0 ]; then
        continue
      fi
      schedule_testing_farm_request
      check_state
      final_report
    done
}

iterate_over_all_containers
