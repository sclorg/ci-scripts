#!/bin/bash

SCL_CONTAINERS="s2i-nodejs-container \
s2i-base-container \
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
mongodb-container \
golang-container
"

TMP_DIR="/tmp/daily_scl_tests"
RESULT_DIR="${TMP_DIR}/results"

if [[ -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR:?}/"
fi
mkdir -p "${RESULT_DIR}"

function clone_repo() {
    local repo_name=$1; shift
    git clone "https://github.com/sclorg/${repo_name}.git"
    cd "${repo_name}" || { echo "Repository ${repo_name} does not exist. Skipping." && return 1 ; }
    git submodule update --init
    git submodule update --remote
}

function iterate_over_all_containers() {
    for repo in ${SCL_CONTAINERS}; do
        cd ${TMP_DIR} || exit
        local log_name="${TMP_DIR}/${repo}.log"
        clone_repo "$repo" && make test TARGET=centos7 > "${log_name}" 2>&1 || mv "${log_name}" "${RESULT_DIR}/"
    done
}

iterate_over_all_containers
