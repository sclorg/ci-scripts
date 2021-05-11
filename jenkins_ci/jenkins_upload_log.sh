#!/bin/bash

# Function uploads log into GitHub gist and update corresponding PR with reference to log
set -ex

CONTEXT=$1
GIT_USER=$2
GIT_PROJECT=$3

GIT_COMMIT=$(git rev-parse HEAD)

curl -Ss "${BUILD_URL}api/json" > build_log.json
curl -Ss "${BUILD_URL}consoleText" > build_log
if [[ $? -ne 0 ]]; then
  python ./ci-scripts/jenkins_ci/github_gist_log.py --force --context="$CONTEXT" --gituser="$GIT_USER" --gitproject="$GIT_PROJECT" --git-commit="$GIT_COMMIT"
fi

python ./ci-scripts/jenkins_ci/github_gist_log.py --context="$CONTEXT" --gituser="$GIT_USER" --gitproject="$GIT_PROJECT" --git-commit="$GIT_COMMIT"

rm build_log build_log.json
