#!/bin/bash

# This script tests image in OpenShift 3 environment
set -ex

TARGET_OS="$1"
if [ x"${TARGET_OS}" == "x" ]; then
  echo "Parameter for image-test-openshift.sh script has to be specified"
  exit 1
fi

# Start local cluster only once for all images, restarting cluster takes long and often fails
tmplib=$(mktemp)
curl https://raw.githubusercontent.com/sclorg/container-common-scripts/master/test-lib-openshift.sh >"$tmplib"
source common/test-lib-openshift.sh
echo "Starting a local cluster before running the tests..."
if ct_os_cluster_up; then
  echo "A local cluster started successfully before running the tests."
else
  echo "ERROR: A local cluster not started before starting the tests."
  exit 1
fi
sleep 10

make test-openshift TARGET="${TARGET_OS}" UPDATE_BASE=1 TAG_ON_SUCCESS=true
