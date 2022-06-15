#!/bin/bash

# The script executes test for RHSCL image.
set -ex

TARGET_OS=$1

make test TARGET="${TARGET_OS}" TAG_ON_SUCCESS=true
for remote in $(git remote | grep test_); do
  git checkout "$remote"/master
  git submodule update --init
  versions=$(grep "VERSIONS = " Makefile | sed "s|VERSIONS = ||")
  echo "Testing ${remote#test_}/master - version ${versions##* }"
  make test TARGET="${TARGET_OS}" VERSIONS="${versions##* }"
done
git checkout -f origin/master
