#!/bin/bash

# Script pushes changes into generated branch if exists
set -ex

if git branch | grep -q generated; then
  GIT_URL=$(git config --get remote.origin.url)
  GIT_URL=${GIT_URL##git://}
  git remote add auth_origin https://$GITHUB_PUSH_TOKEN@\$GIT_URL
  git push auth_origin generated
fi
