#!/bin/bash

# This script adds git config configuration file into environment
# it also updates generated branch and shows diff
set -ex

git config --global user.name "SCLorg Jenkins"
git config --global user.email "sclorg@redhat.com"
cd sources
if git ls-remote --exit-code origin generated &>/dev/null; then
  ./common/update-generated.sh
  git diff origin/generated..generated
fi
