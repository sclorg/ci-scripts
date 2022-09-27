#!/bin/bash

# Scripts prepares docker for using on CentOS

set -ex
# Prepare docker

sed -i "s|OPTIONS='|OPTIONS='--insecure-registry 172.30.0.0/16 |" /etc/sysconfig/docker; iptables -F
service docker start

# Enable sudo for ssh (required by test cases)
sed -i -e "s|Defaults    requiretty||" /etc/sudoers
