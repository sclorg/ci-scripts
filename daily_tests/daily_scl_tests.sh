#!/bin/bash

SCL_CONTAINERS="s2i-php-container \
s2i-perl-container \
s2i-ruby-container \
s2i-python-container \
container-common-scripts \
s2i-nodejs-container \
s2i-base-container"

TMP_DIR="/tmp/daily_scl_tests"
RESULT_DIR="${TMP_DIR}/results"

if [[ -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR}/"
fi
mkdir -p "${RESULT_DIR}"

function clone_repo() {
    local repo_name=$1; shift
    git clone "https://github.com/sclorg/${repo_name}.git"
    cd ${repo_name}
    git submodule update --init
}

function iterate_over_all_containers() {
    for repo in ${SCL_CONTAINERS}; do
        cd ${TMP_DIR}
        local log_name="${TMP_DIR}/${repo}.log"
        clone_repo "$repo"
        make test CUSTOM_REPO=/vagrant/repos7 TARGET=rhel7 > "${log_name}" 2>&1
        if [[ $? -ne 0 ]]; then
            cp "${log_name}" "${RESULT_DIR}/"
        fi
    done
}

iterate_over_all_containers
