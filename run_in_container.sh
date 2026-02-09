#!/bin/bash

set -x

TARGET=$1
TESTS=$2

podman run --rm -it \
  -v /var/tmp/:/var/tmp/:Z \
  -e SHARED_DIR=/var/tmp/ \
  -e TARGET=$TARGET \
  -e TESTS=$TESTS \
  quay.io/sclorg/daily-tests:latest
