#!/bin/bash

set -x

[[ -z "$1" ]] && { echo "You have to specify target to build SCL images. centos7, rhel7 or fedora" && exit 1 ; }
TARGET="$1"
shift
[[ -z "$1" ]] && { echo "You have to specify type of the test to run. test, test-openshift, test-openshift-4" && exit 1 ; }
TESTS="$1"

TMP_DIR="/tmp/daily_scl_tests-$TARGET-$TESTS"
RESULT_DIR="${TMP_DIR}/results/"
ls -la "${RESULT_DIR}"

SUBJECT="RHSCL nightly build testing for target ${TARGET}-${TESTS}"
ls -A "${RESULT_DIR}"
if [[ -z $(ls -A "${RESULT_DIR}") ]]; then
  mail -s "${SUBJECT} was successful" -r phracek@redhat.com phracek@redhat.com zmiklank@redhat.com
else
  SUBJECT="${SUBJECT} failed."
  MESSAGE="${SUBJECT}\n"
  cd "${RESULT_DIR}" || exit 1
  ATTACHMENTS=""
  ls -1 *.log
  for log in `ls -1 *.log`; do
    MESSAGE="${MESSAGE}- ${log}\n"
    ATTACHMENTS="${ATTACHMENTS} -a ${RESULT_DIR}/$log"
  done
  echo -e "${MESSAGE}" | mail -s "${SUBJECT}" ${ATTACHMENTS} -r phracek@redhat.com phracek@redhat.com zmiklank@redhat.com pkubat@redhat.com hhorak@redhat.com lbalhar@redhat.com
  #python ./send_results.py "${RESULT_DIR}" "${TARGET}" "${TESTS}" phracek@redhat.com phracek@redhat.com pkubat@redhat.com hhorak@redhat.com lbalhar@redhat.com zmiklank@redhat.com
fi
