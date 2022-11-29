#!/bin/bash

set -x

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
mysql-container
"

[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. centos7, rhel7 or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-openshift, test-openshift-4" && exit 1 ; }
TESTS="$1"

CUR_WD=$(pwd)
echo "Current working directory is: ${CUR_WD}"
echo "List is:"
ls -la

TMP_DIR="/tmp/daily_scl_tests-$TARGET-$TESTS"
RESULT_DIR="${TMP_DIR}/results/"
KUBECONFIG=/root/.kube/config
KUBEPASSWD=/root/.kube/ocp-kube
REQ_ID=""
if [[ -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR:?}/"
fi

mkdir -p "${RESULT_DIR}"

function clone_repo() {
    local repo_name=$1; shift
    # Sometimes cloning failed with an error
    # The requested URL returned error: 500. Save it into log for info
    git clone "https://github.com/sclorg/${repo_name}.git" || \
        { echo "Repository ${repo_name} was not clonned." > ${RESULT_DIR}/${repo_name}.log; return 1 ; }
    cd "${repo_name}" || { echo "Repository ${repo_name} does not exist. Skipping." && return 1 ; }
    git submodule update --init
    git submodule update --remote
}

function clean_ocp4() {
    if [[ "${TESTS}" == "test-openshift-4" ]]; then
      oc project default
      PASS=$(cat "${KUBEPASSWD}")
      oc login --username=kubeadmin --insecure-skip-tls-verify=true --password="${PASS}" --server=https://api.core-serv-ocp.hosted.psi.rdu2.redhat.com:6443
      export PATH="/usr/local/oc-v4/bin:$PATH"
      oc projects | grep sclorg | xargs oc delete projects
      oc delete all --all
      # Sleep couple seconds till OpenShift is not back again.
      sleep 10
    fi
}

function iterate_over_all_containers() {
    for repo in ${SCL_CONTAINERS}; do
      REQ_ID=""
      cd ${TMP_DIR} || exit
      local log_name="${TMP_DIR}/${repo}.log"
      clone_repo "${repo}"
      make "${TESTS}" TARGET="${TARGET}" > "${log_name}" 2>&1
      if [[ $? -ne 0 ]]; then
          cp "${log_name}" "${RESULT_DIR}/"
      fi
      clean_ocp4
    done
}
if [[ "${TESTS}" == "test-openshift-4" ]]; then
  # Download kubeconfig
  curl -L https://url.corp.redhat.com/ocp4-kubeconfig >$KUBECONFIG
  # Download kubepasswd
  curl -L https://url.corp.redhat.com/ocp4-kubepasswd >$KUBEPASSWD
fi

iterate_over_all_containers

cd "${CUR_WD}"

./daily_tests/send_email.sh "${TARGET}" "${TESTS}"
