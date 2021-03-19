#!/bin/bash

set -ex

CONTEXT=$1
GIT_USER=$2
GIT_PROJECT=$3

pull_number=$(jq -r '.issue.number' <<< "$CI_MESSAGE")
git fetch origin +refs/pull/*:refs/remotes/origin/pr/*
git checkout origin/pr/$pull_number/head

GIT_COMMIT=$(git rev-parse HEAD)

python "${CI_SCRIPTS}"/update_github_pr.py --context="$CONTEXT" --gituser="$GIT_USER" --gitproject="$GIT_PROJECT" --git-commit="$GIT_COMMIT"
