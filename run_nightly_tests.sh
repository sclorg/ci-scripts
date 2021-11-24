#!/bin/bash

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

curl -L https://url.corp.redhat.com/fmf-data > /tmp/fmf_data
source /tmp/fmf_data

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
      "name": "nightly-container-$TARGET"
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
  cat request.json
  curl $TF_ENDPOINT/requests --data @request.json --header "Content-Type: application/json" --output response.json
  cat response.json
  REQ_ID=$(jq -r .id response.json)
  echo "$REQ_ID"
}

function check_testing_farm_status() {
  echo "Check state for $REQ_ID"
  CMD="$TF_ENDPOINT/requests/$REQ_ID"
  curl $CMD > job.json
  state=$(jq -r .state job.json)
  # Wait till job is not finished. As soon as state is complete or failure then go to the finish action
  while [ "$state" == "running" ] || [ "$state" == "new" ] || [ "$state" == "pending" ] || [ "$state" == "queued" ]; do
    # Wait 60s. We do not need to query Testing Farm each second
    sleep 60
    curl $CMD > job.json
    state=$(jq -r .state job.json)
  cat job.json
  done
}

schedule_testing_farm_request

check_testing_farm_status

final_report
