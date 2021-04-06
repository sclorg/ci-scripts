#!/bin/bash

set -ex

CONTEXT=$1
GIT_USER=$2
GIT_PROJECT=$3

if [ x"${CONTEXT}" == "x" ]; then
  echo "The first parameter CONTEXT to upload_diff.sh has to be specified."
  exit 1
fi

if [ x"${CONTEXT}" == "xcentos7" ] || [ x"${CONTEXT}" == "xfedora" ]; then
  echo "We do not use github2fedmsg in CentOS CI."
  exit 0
fi

if [ x"${GITUSER}" == "x" ]; then
  echo "The second parameter GITUSER to upload_diff.sh has to be specified."
  exit 1
fi

if [ x"${GITPROJECT}" == "x" ]; then
  echo "The third parameter GITPROJECT to upload_diff.sh has to be specified."
  exit 1
fi


pull_number=$(jq -r '.issue.number' <<< "$CI_MESSAGE")
git fetch origin +refs/pull/*:refs/remotes/origin/pr/*
git checkout origin/pr/$pull_number/head

GIT_COMMIT=$(git rev-parse HEAD)

python "${CI_SCRIPTS}"/update_github_pr.py --context="$CONTEXT" --gituser="$GIT_USER" --gitproject="$GIT_PROJECT" --git-commit="$GIT_COMMIT"
