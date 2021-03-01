#!/bin/bash

# The script executes test for RHSCL image.
# The script executes also conu tests if they are present
set -ex

TARGET_OS=$1
cd sources

function run_conu() {
    if [ -f ./test/run-conu ]; then
      if [ "${TARGET_OS}" == "fedora" ] || [ "${TARGET_OS}" == "centos7" ] ; then
          make test-with-conu TARGET="${TARGET_OS}" TAG_ON_SUCCESS=true
      fi
    fi
}
make test TARGET="${TARGET_OS}" UPDATE_BASE=1 TAG_ON_SUCCESS=true
run_conu
for remote in $(git remote | grep test_); do
  git checkout "$remote"/master
  git submodule update --init
  versions=$(grep "VERSIONS = " Makefile | sed "s|VERSIONS = ||")
  echo "Testing ${remote#test_}/master - version ${versions##* }"
  make test TARGET="${TARGET_OS}" VERSIONS="${versions##* }"
  run_conu
done
git checkout -f origin/master
