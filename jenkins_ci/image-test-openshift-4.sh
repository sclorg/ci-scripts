#!/bin/bash

# This script tests image in OpenShift 4 environment
set -ex

TARGET_OS="$1"
if [ x"${TARGET_OS}" == "x" ]; then
  echo "Parameter for image-test-openshift-4.sh script has to be specified"
  exit 1
fi
# Download kubeconfig
curl -L https://url.corp.redhat.com/ocp-kubeconfig >/root/.kube/config
# Download kubepasswd
curl -L https://url.corp.redhat.com/kube >/root/.kube/ocp-kube

make test-openshift-4 TARGET="${TARGET_OS}" UPDATE_BASE=1 TAG_ON_SUCCESS=true
