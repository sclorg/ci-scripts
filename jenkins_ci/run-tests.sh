#!/bin/bash

set -ex

TARGET_OS=$1
cd sources

make test TARGET=${TARGET_OS} UPDATE_BASE=1 TAG_ON_SUCCESS=true
[ -f ./test/run-conu ] && [ "${TARGET_OS}" != "rhel8" ] && make test-with-conu TARGET=${TARGET_OS} TAG_ON_SUCCESS=true
for remote in $(git remote | grep test_); do
  git checkout $remote/master
  git submodule update --init
  versions=$(grep "VERSIONS = " Makefile | sed "s|VERSIONS = ||")
  echo "Testing ${remote#test_}/master - version ${versions##* }"
  make test TARGET=${TARGET_OS} VERSIONS=${versions##* }
  [ -f ./test/run-conu ] && [ "${TARGET_OS}" != "rhel8" ] && make test-with-conu TARGET=${TARGET_OS} TAG_ON_SUCCESS=true
done
git checkout -f origin/master
