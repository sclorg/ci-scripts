#!/bin/bash

# Function uploads log into GitHub gist and update corresponding PR with reference to log
set -ex

CONTEXT=$1
GIT_USER=$2
GIT_PROJECT=$3

GIT_COMMIT=$(git rev-parse HEAD)

curl -Ss "$BUILD_URL/consoleText" > build_log
curl -Ss "$BUILD_URL/api/json" > build_log.json

python "${CI_SCRIPTS}"/upload_log.py "$CONTEXT" "$GIT_USER" "$GIT_PROJECT" "$GIT_COMMIT"

rm build_log build_log.json
