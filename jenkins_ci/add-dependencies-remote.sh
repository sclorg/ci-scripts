#!/bin/bash

set -ex

curl --silent https://raw.githubusercontent.com/sclorg/rhscl-container-ci/master/configuration | while read scl namespace gituser gitproject trigger hub_namespace; do

  if [[ "${trigger}" == *{name}* ]]; then
    echo "Adding and fetching test_${scl}-${namespace} remote"
    git remote add "test_${scl}-${namespace}" git://github.com/${gituser}/${gitproject}.git
    git fetch "test_${scl}-${namespace}"
  fi

done
