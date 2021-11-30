#!/bin/bash

LOGS_DIR="/home/fedora/logs"
[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. centos7, rhel7 or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-openshift, test-openshift-4" && exit 1 ; }
TESTS="$1"

if [[ "$TARGET" == "rhel8" ]]; then
  COMPOSE="RHEL-8-Updated"
elif [[ "$TARGET" == "rhel7" ]]; then
  COMPOSE="RHEL-7-LatestUpdated"
elif [[ "$TARGET" == "centos7" ]]; then
  COMPOSE="CentOS-7-latest"
  TESTING_TARGET="${TARGET}"
elif [[ "$TARGET" == "fedora" ]]; then
  COMPOSE="CentOS-7-latest"
else
  echo "This target is not supported"
  exit 1
fi

if [[ "$TESTS" != "test" ]] && [[ "$TESTS" != "test-openshift" ]] && [[ "$TESTS" != "test-openshift-4" ]]; then
  echo "This test scenario is not enabled."
  exit 1
fi

JOB_JSON="job-${TARGET}.json"
REQUEST_JSON="request-${TARGET}.json"
RESPONSE_JSON="response-${TARGET}.json"
cd /home/fedora
if [[ ! -d "${LOGS_DIR}" ]]; then
  mkdir -p "${LOGS_DIR}"
fi

LOG="${LOGS_DIR}/$TARGET-$TESTS.log"
date > ${LOG}
curl -L https://url.corp.redhat.com/fmf-data > /tmp/fmf_data
source /tmp/fmf_data

echo "TARGET is: ${TARGET} and test is: ${TESTS}" | tee -a ${LOG}

function final_report() {
  echo "FINAL REPORT for ${REQ_ID}" | tee -a ${LOG}
  curl $TF_ENDPOINT/requests/$REQ_ID > "${JOB_JSON}"
  cat "${JOB_JSON}" | tee -a ${LOG}
  state=$(jq -r .state "${JOB_JSON}")
  result=$(jq -r .result.overall "${JOB_JSON}")
  echo "STATE: $state" | tee -a ${LOG}
  echo "RESULT: $result" | tee -a ${LOG}
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
  echo "New State: $new_state" | tee -a ${LOG}
  echo "Infra state: $infra_error" | tee -a ${LOG}
}


function schedule_testing_farm_request() {
  echo "Schedule job for: $TARGET" | tee -a ${LOG}
  TESTING_PLAN="${TARGET}"
  if [[ "$TARGET" == "fedora" ]]; then
    TESTING_PLAN="centos7"
  fi
  cat << EOF > ${REQUEST_JSON}
    {
      "api_key": "$API_KEY",
      "test": {"fmf": {
      "url": "https://gitlab.cee.redhat.com/platform-eng-core-services/sclorg-tmt-plans",
      "ref": "master",
      "name": "nightly-container-${TESTING_PLAN}"
      }},
      "environments": [{
      "arch": "x86_64",
      "os": {"compose": "$COMPOSE"},
      "variables": {
        "TEST": "$TESTS",
        "OS": "$TARGET"
      }}]
    }
EOF
  cat "${REQUEST_JSON}" | tee -a ${LOG}
  curl $TF_ENDPOINT/requests --data @${REQUEST_JSON} --header "Content-Type: application/json" --output "${RESPONSE_JSON}"
  REQ_ID=$(jq -r .id "${RESPONSE_JSON}")
  echo "$REQ_ID" | tee -a ${LOG}
}

function check_testing_farm_status() {
  echo "Check state for $REQ_ID" | tee -a ${LOG}
  CMD="$TF_ENDPOINT/requests/$REQ_ID"
  echo "Command for checking state is: ${CMD}" | tee -a ${LOG}
  curl $CMD > "${JOB_JSON}"
  state=$(jq -r .state "${JOB_JSON}")
  # Wait till job is not finished. As soon as state is complete or failure then go to the finish action
  while [ "$state" == "running" ] || [ "$state" == "new" ] || [ "$state" == "pending" ] || [ "$state" == "queued" ]; do
    # Wait 300s. We do not need to query Testing Farm each second
    sleep 300
    curl $CMD > "${JOB_JSON}"
    state=$(jq -r .state "${JOB_JSON}")
    date | tee -a ${LOG}
    echo "$state" | tee -a ${LOG}
  done
}

schedule_testing_farm_request

check_testing_farm_status

final_report
