#!/usr/bin/env bash

set -x

OS=$1
[[ -z $OS ]] && { echo "OS for checking grades was not specified." && echo "Command is: $0 <RHEL7|RHEL8>" && exit 1 ; }

LOGS_DIR="/home/fedora/logs"
SCRIPT_LOG="$LOGS_DIR/grades.log"
GRADE_FLAG=0
if [[ "$OS" == "RHEL7" ]]; then
  GRADES_LOG="$HOME/logs/rhel8-grades"
  RHCWT_CONFIG="rhel7.yaml"

elif [[ "$OS" == "RHEL8" ]]; then
  GRADES_LOG="$HOME/logs/rhel8-grades"
  RHCWT_CONFIG="rhel8.yaml"
fi

date | tee $SCRIPT_LOG

echo "Configuration file is $RHCWT_CONFIG and logs are in $GRADES_LOG" | tee -a "${SCRIPT_LOG}"
SUMMARY="Grades for"
function check_grades() {
  echo "GRADE_FLAG: $GRADE_FLAG" | tee -a "${SCRIPT_LOG}"
  while read -r line; do
    echo "X $line X"
    if [[ ! "$line" == *"[A]"* ]]; then
      GRADE_FLAG=1
      echo "GRADE_FLAG: $GRADE_FLAG" | tee -a "${SCRIPT_LOG}"
    fi
  done < "$GRADES_LOG"
  return $GRADE_FLAG
}

function get_grades() {
  rhcwt --base WHATEVER --config "$RHCWT_CONFIG" rhcc grades > "$GRADES_LOG"
  tee -a "${SCRIPT_LOG}" < "${GRADES_LOG}"
  return 0
}

get_grades

if ! check_grades; then
  echo "Container grades are not all in state [A] $OS" | tee -a "${SCRIPT_LOG}"
  SUMMARY="$SUMMARY $OS are NOT ok. Some of them are not in Grade A."
else
  echo "Container grades are all in state [A]" | tee -a "${SCRIPT_LOG}"
  SUMMARY="$SUMMARY $OS are all in Grade A."
fi

mail -s "$SUMMARY" -r phracek@redhat.com phracek@redhat.com pkubat@redhat.com hhorak@redhat.com < "${GRADES_LOG}"
