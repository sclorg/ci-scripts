#!/bin/bash

set -x

SCL_CONTAINERS_UPSTREAM="\
s2i-nodejs-container
"

SCL_CONTAINERS="\
httpd-container
s2i-base-container
s2i-nodejs-container
s2i-php-container
s2i-perl-container
s2i-ruby-container
s2i-python-container
varnish-container
nginx-container
redis-container
mariadb-container
postgresql-container
valkey-container
mysql-container
"

[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. rhel9, rhel8, or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-openshift, test-openshift-pytest, test-openshift-4" && exit 1 ; }
TESTS="$1"
shift
CUR_WD=$(pwd)
echo "Current working directory is: ${CUR_WD}"

TMP_DIR="${TMT_PLAN_DATA}"
RESULT_DIR="${TMP_DIR}/results/"
KUBECONFIG=/root/.kube/config
KUBEPASSWD=/root/.kube/ocp-kube

mkdir -p "${RESULT_DIR}"

function clone_repo() {
    local repo_name=$1; shift
    # Sometimes cloning failed with an error
    # The requested URL returned error: 500. Save it into log for info
    git clone "https://github.com/sclorg/${repo_name}.git" || \
        { echo "Repository ${repo_name} was not cloned." > ${RESULT_DIR}/${repo_name}.log; return 1 ; }
    cd "${repo_name}" || { echo "Repository ${repo_name} does not exist. Skipping." && return 1 ; }
    git submodule update --init
    git submodule update --remote
}

function clean_ocp4() {
    if [[ "${TESTS}" == "test-openshift-4" ]] || [[ "${TESTS}" == "test-openshift-pytest" ]]; then
      echo "Cleaning OpenShift 4 environment"
      oc project default
      PASS=$(cat "${KUBEPASSWD}")
      oc login --username=kubeadmin --insecure-skip-tls-verify=true --password="${PASS}" --server=https://api.core-serv-ocp.hosted.psi.rdu2.redhat.com:6443
      export PATH="/usr/local/oc-v4/bin:$PATH"
      oc project default
      oc projects | grep sclorg
      # oc projects | grep sclorg | xargs oc delete project
      # oc delete all --all
      # Sleep couple seconds till OpenShift is not back again.
      sleep 10
    fi
}

function iterate_over_all_containers() {
  CONTAINTERS_TO_TEST=$SCL_CONTAINERS
  if [[ "${TESTS}" == "test-upstream" ]]; then
    CONTAINTERS_TO_TEST=$SCL_CONTAINERS_UPSTREAM
  fi


  for repo in ${CONTAINTERS_TO_TEST}; do
    # Do not shutting down OpenShift 3 cluster
    export OS_CLUSTER_STARTED_BY_TEST=0
    cd ${TMP_DIR} || exit
    local log_name="${TMP_DIR}/${repo}.log"
    clone_repo "${repo}"
    if [[ -d "/root/sclorg-tmt-plans" ]]; then
      pushd /root/sclorg-tmt-plans && ./set_devel_repo.sh "sclorg/${repo}" "$TARGET" "${TMP_DIR}/${repo}"
      # Switch back to tmp container-repo name
      popd
    fi
    DEBUG=true make "${TESTS}" TARGET="${TARGET}" > "${log_name}" 2>&1
    if [[ $? -ne 0 ]]; then
      echo "Tests for container $repo has failed."
      cp "${log_name}" "${RESULT_DIR}/"
      echo "Show the last 100 lines from file: ${RESULT_DIR}/${repo}.log"
      tail -100 "${RESULT_DIR}/${repo}.log"
    fi
    clean_ocp4
  done
}

git clone https://gitlab.cee.redhat.com/platform-eng-core-services/sclorg-tmt-plans /root/sclorg-tmt-plans
git clone https://github.com/sclorg/container-common-scripts.git /root/container-common-scripts


if [[ "${TESTS}" == "test-openshift-4" ]] || [[ "${TESTS}" == "test-openshift-pytest" ]]; then
    echo "Testing OpenShift 4 is enabled"
    curl -L --insecure https://url.corp.redhat.com/sclorg-data-kubeconfig >$KUBECONFIG
    # Download kubepasswd
    curl -L --insecure https://url.corp.redhat.com/sclorg-data-kubepasswd >$KUBEPASSWD
fi

iterate_over_all_containers

cd "${CUR_WD}"
