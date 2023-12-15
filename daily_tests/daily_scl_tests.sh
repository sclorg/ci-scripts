#!/bin/bash

set -x

SCL_CONTAINERS_UPSTREAM="\
s2i-nodejs-container
"
SCL_CONTAINERS="\
s2i-base-container
s2i-nodejs-container
s2i-php-container
s2i-perl-container
s2i-ruby-container
s2i-python-container
varnish-container
nginx-container
httpd-container
redis-container
mariadb-container
postgresql-container
"
# Disable mysql-container
# ---> 12:22:24     Storing version '8.0.32' information into the data dir '/var/lib/mysql/data/mysql_upgrade_info'
  #=> sourcing 50-passwd-change.sh ...
  #---> 12:23:07     Setting passwords ...
  #---> 12:26:30     Shutting down MySQL ...
  #mysqladmin: reload failed; error: 'Lost connection to MySQL server during query'
  #/usr/share/container-scripts/mysql/common.sh: line 100:    74 Killed                  ${MYSQL_PREFIX}/libexec/mysqld --defaults-file=$MYSQL_DEFAULTS_FILE --skip-networking --socket=$MYSQL_LOCAL_SOCKET "$@"
  #Test for image 'rhel8/mysql-80:1' FAILED (exit code: 1)
  #    Created container 65a87f95db0c6e2fc513543e2daff9acfe8916b2bc4c32d8bcee2301309bd82e
  #  Testing MySQL connection to 10.88.11.184...

[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. centos7, rhel7 or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-openshift, test-openshift-4" && exit 1 ; }
TESTS="$1"

CUR_WD=$(pwd)
echo "Current working directory is: ${CUR_WD}"

TMP_DIR="${TMT_PLAN_DATA}"
RESULT_DIR="${TMP_DIR}/results/"
KUBECONFIG=/root/.kube/config
KUBEPASSWD=/root/.kube/ocp-kube

mkdir -p "${RESULT_DIR}"

function start_ocp3() {
    cd /root/container-common-scripts || exit 1
    bash test-lib-openshift.sh ct_os_cluster_up
}

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
    if [[ "${TESTS}" == "test-openshift-4" ]]; then
      echo "Cleaning OpenShift 4 environment"
      oc project default
      PASS=$(cat "${KUBEPASSWD}")
      oc login --username=kubeadmin --insecure-skip-tls-verify=true --password="${PASS}" --server=https://api.core-serv-ocp.hosted.psi.rdu2.redhat.com:6443
      export PATH="/usr/local/oc-v4/bin:$PATH"
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
    make "${TESTS}" TARGET="${TARGET}" > "${log_name}" 2>&1
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


if [[ "${TESTS}" == "test-openshift-4" ]]; then
    echo "Testing OpenShift 4 is enabled"
    # Download kubeconfig
    curl -L https://url.corp.redhat.com/ocp4-kubeconfig >$KUBECONFIG
    # Download kubepasswd
    curl -L https://url.corp.redhat.com/ocp4-kubepasswd >$KUBEPASSWD
fi

if [[ "${TESTS}" == "test-openshift" ]]; then
    echo "Starting cluster on Nightly Build request"
    start_ocp3
fi

iterate_over_all_containers

cd "${CUR_WD}"
