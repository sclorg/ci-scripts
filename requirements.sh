#!/bin/bash

set -ex

useradd -u 500 -r -g 0 -m -s /bin/bash -c "Default Application User" "${NAME}"
chown -R 500:0 "${HOME}"
chmod -R a+rwx "${HOME}"
