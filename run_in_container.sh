#!/bin/bash

set -x

TARGET=$1
TESTS=$2
TEST_TYPE=$3

podman run --rm -it \
  -v /var/tmp/:/var/tmp/:Z \
  -e SHARED_DIR=/var/tmp/ \
  -e TARGET=$TARGET \
  -e TESTS=$TESTS \
  -e TEST_TYPE=$TEST_TYPE \
  quay.io/sclorg/daily-tests:latest
