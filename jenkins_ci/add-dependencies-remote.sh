#!/bin/bash

# This script adds remote github directory from git://github.com/sclorg/<project>
# into current one.
# The script also fetches the latest changes from github repository
# The script is used for s2i-base-container.
# param: Specify trigger name, like s2i-rh
set -ex

name="$1"

if [ x"${name}" == "x" ]; then
  echo "Parameter for add-dependencies-remote.sh script has to be specified"
  exit 1
fi
curl --silent https://raw.githubusercontent.com/sclorg/rhscl-container-ci/master/configuration | while read scl namespace gituser gitproject trigger hub_namespace; do

  if [[ "${trigger}" == *"${name}"* ]]; then
    echo "Adding and fetching test_${scl}-${namespace} remote"
    git remote add "test_${scl}-${namespace}" git://github.com/${gituser}/${gitproject}.git
    git fetch "test_${scl}-${namespace}"
  fi

done
