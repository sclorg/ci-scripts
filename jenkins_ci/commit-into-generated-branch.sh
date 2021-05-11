#!/bin/bash

# This script adds git config configuration file into environment
# it also updates generated branch and shows diff
set -ex

pushd .. > /dev/null
git config --global user.name "SCLorg Jenkins"
git config --global user.email "sclorg@redhat.com"

popd >> /dev/null

if git ls-remote --exit-code origin generated &>/dev/null; then
  ./common/update-generated.sh
  git diff origin/generated..generated
fi

# ./common/update-generated.sh deletes ci-scripts for some reason.
# It needs to be fixed
if [[ ! -d "ci-scripts" ]]; then
  git clone https://github.com/sclorg/ci-scripts.git ci-scripts
fi
