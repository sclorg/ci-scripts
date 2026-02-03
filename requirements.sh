#!/bin/bash

set -ex

useradd -u 900 -r -g 0 -m -s /bin/bash -c "Default Application User" "${NAME}"
chown -R 900:0 "${HOME}"
chmod -R a+rwx "${HOME}"
