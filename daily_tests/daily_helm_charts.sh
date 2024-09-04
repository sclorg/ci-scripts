#!/bin/bash

set -x

HELM_CHARTS="\
httpd
mariadb
mysql
nginx
postgresql
redis
php
perl
nodejs
ruby
python
valkey
"
TMP_DIR="${TMT_PLAN_DATA}"
RESULT_DIR="${TMP_DIR}/results/"
KUBECONFIG=/root/.kube/config
KUBEPASSWD=/root/.kube/ocp-kube

mkdir -p "${RESULT_DIR}"

function clone_repo() {
    local repo_name="helm-charts"
    # Sometimes cloning failed with an error
    # The requested URL returned error: 500. Save it into log for info
    git clone "https://github.com/sclorg/${repo_name}.git" || \
        { echo "Repository ${repo_name} was not cloned." > ${RESULT_DIR}/${repo_name}.log; return 1 ; }
    cd "${repo_name}" || { echo "Repository ${repo_name} does not exist. Skipping." && return 1 ; }
}

function iterate_over_all_helm_charts() {

  for helm in ${HELM_CHARTS}; do
    # Do not shutting down OpenShift 3 cluster
    export OS_CLUSTER_STARTED_BY_TEST=0
    local log_name="${TMP_DIR}/helm-chart-${helm}.log"
    make "test-${helm}" > "${log_name}" 2>&1
    if [[ $? -ne 0 ]]; then
      echo "Tests for helm $helm has failed."
      cp "${log_name}" "${RESULT_DIR}/"
      echo "Show the last 100 lines from file: ${RESULT_DIR}/${log_name}.log"
      tail -100 "${RESULT_DIR}/${log_name}.log"
    fi
  done
}

git clone https://gitlab.cee.redhat.com/platform-eng-core-services/sclorg-tmt-plans /root/sclorg-tmt-plans
git clone https://github.com/sclorg/container-common-scripts.git /root/container-common-scripts

echo "Testing OpenShift 4 is enabled"
# Download kubeconfig
curl -L --insecure https://url.corp.redhat.com/sclorg-data-kubeconfig >$KUBECONFIG
# Download kubepasswd
curl -L --insecure https://url.corp.redhat.com/sclorg-data-kubepasswd >$KUBEPASSWD

clone_repo

iterate_over_all_helm_charts

cd "${CUR_WD}"
