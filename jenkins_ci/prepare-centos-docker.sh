#!/bin/bash

# Scripts prepares docker for using on CentOS

set -ex
# Prepare docker
# WORKAROUND - installing go-md2man tool from cbs directly, all golang packages were removed from repos (golang is deprecated in latest RHEL7)
#              https://wiki.centos.org/Manuals/ReleaseNotes/CentOS7.1810#head-e467ac744557df926ed56dc0106f43961e5ffc38
yum -y install docker perl git centos-release-scl-rh rsync groff-base centos-release-openshift-origin epel-release \
                        http://cbs.centos.org/kojifiles/packages/golang-github-cpuguy83-go-md2man/1.0.4/4.0.el7/x86_64/golang-github-cpuguy83-go-md2man-1.0.4-4.0.el7.x86_64.rpm
# WORKAROUND - until http://cbs.centos.org/koji/buildinfo?buildID=24652 is released (fedora based images fails now)
yum -y install  http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-1.13.1-87.git07f3374.el7.x86_64.rpm \
                        http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-client-1.13.1-87.git07f3374.el7.x86_64.rpm \
                        http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-common-1.13.1-87.git07f3374.el7.x86_64.rpm \
                        http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-rhel-push-plugin-1.13.1-87.git07f3374.el7.x86_64.rpm

yum -y install rh-python36-python-virtualenv origin-clients distgen \
              https://kojipkgs.fedoraproject.org//packages/source-to-image/1.1.7/3.fc29/x86_64/source-to-image-1.1.7-3.fc29.x86_64.rpm #source-to-image

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
