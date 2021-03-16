#!/bin/bash

# The script upload diff file from origin/generated against generated branch
# The first part uploads diff into GitHub gist
# The second part updates PR with status
set -ex

TRIGGER_PHRASE=$1
GITUSER=$2
GITPROJECT=$3

if [ x"${TRIGGER_PHRASE}" == "x" ]; then
  echo "The first parameter TRIGGER_PHRASE to upload_diff.sh has to be specified."
  exit 1
fi

if [ x"${GITUSER}" == "x" ]; then
  echo "The second parameter GITUSER to upload_diff.sh has to be specified."
  exit 1
fi

if [ x"${GITPROJECT}" == "x" ]; then
  echo "The third parameter GITPROJECT to upload_diff.sh has to be specified."
  exit 1
fi

ssh -F ssh_config host "set -e; cd sources; \
  if git branch | grep -q generated; then \
    git diff origin/generated..generated; \
  fi;" > diff

# Generate diff only once and only if something differs
if [[ "${TRIGGER_PHRASE}" != 'test' ]] || [[ ! -s diff ]] || [[ -z "${GITHUB_TOKEN:-}" ]]; then
  exit 0;
fi

GIT_COMMIT=$(git rev-parse HEAD)
GITHUB_USERNAME="rhscl-automation"
COMMIT_JSON=$(curl -u ${GITHUB_USERNAME}:"$GITHUB_TOKEN" -s https://api.github.com/repos/"${GITUSER}"/"${GITPROJECT}"/commits/"${GIT_COMMIT}")
COMMIT_URL=$(echo "${COMMIT_JSON}" | python -c "import sys, json; api_res=json.load(sys.stdin); print api_res['html_url'];")

# Uploads diff into GitHub gist
python "${CI_SCRIPTS}"/upload_diff.py "${COMMIT_URL}" "${GITPROJECT}"

. diff_url.prop

#Update PR status
python "${CI_SCRIPTS}"/upload_diff_status.py "${GIT_COMMIT}" "${GITUSER}" "${GITPROJECT}"

rm diff
