#!/bin/bash

# Scripts prepares docker for using on CentOS

set -ex
# Prepare docker

sed -i "s|OPTIONS='|OPTIONS='--insecure-registry 172.30.0.0/16 |" /etc/sysconfig/docker; iptables -F
service docker start

# Install docker-squash
scl enable rh-python36 -- virtualenv --python python3 /usr/local/python-tools
. /usr/local/python-tools/bin/activate
pip install docker-squash
echo ". /usr/local/python-tools/bin/activate" > /root/.bashrc
# Hack docker-squash --version - 1.0.5 is required
# (TEMPORARY FIX - until all images contain fixed https://github.com/sclorg/container-common-scripts/pull/100
# https://github.com/sclorg/container-common-scripts/issues/101)
echo 'docker-squash() { if [ "$1" == "--version" ]; then echo "1.0.5"; else eval $(which docker-squash) $@ 1>&2; fi }' >> /root/.bashrc
echo 'export -f docker-squash' >> /root/.bashrc

# Enable sudo for ssh (required by test cases)
sed -i -e "s|Defaults    requiretty||" /etc/sudoers
