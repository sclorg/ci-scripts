#!/bin/bash

# The script prepares CentOS 7 machine for testing SCL images
# it creates ssh_config file and ./cleanup.sh file
# It also copies sources into OpenStack Slave machine
set -ex

cico node get -f value --retry-count 5 --retry-interval 60 --arch x86_64 --release 7 --count 1 --api-key $(cat ~/duffy.key) | tee cico.out
tail -n 1 cico.out | cut -d ' ' -f 7 > ssid
tail -n 1 cico.out | cut -d ' ' -f 2 > host
h=$(head -n 1 host)
rm cico.out

# Prepare ssh_config
cat > ssh_config << EOF
UserKnownHostsFile /dev/null
StrictHostKeyChecking no
User root
ConnectTimeout 10

Host host
  Hostname ${h}.ci.centos.org
EOF

# Create script for cleanup
cat > .cleanup.sh << EOF
#!/bin/bash
set -ex

cico node done --api-key $(cat ~/duffy.key) $(cat ssid)
rm ssid ssh_config
EOF
chmod a+x .cleanup.sh

# WORKAROUND - installing go-md2man tool from cbs directly, all golang packages were removed from repos (golang is deprecated in latest RHEL7)
#              https://wiki.centos.org/Manuals/ReleaseNotes/CentOS7.1810#head-e467ac744557df926ed56dc0106f43961e5ffc38
ssh -F ssh_config host yum -y install docker perl git centos-release-scl-rh rsync groff-base centos-release-openshift-origin epel-release \
                        http://cbs.centos.org/kojifiles/packages/golang-github-cpuguy83-go-md2man/1.0.4/4.0.el7/x86_64/golang-github-cpuguy83-go-md2man-1.0.4-4.0.el7.x86_64.rpm
# WORKAROUND - until http://cbs.centos.org/koji/buildinfo?buildID=24652 is released (fedora based images fails now)
ssh -F ssh_config host yum -y install  http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-1.13.1-87.git07f3374.el7.x86_64.rpm \
                        http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-client-1.13.1-87.git07f3374.el7.x86_64.rpm \
                        http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-common-1.13.1-87.git07f3374.el7.x86_64.rpm \
                        http://cbs.centos.org/kojifiles/packages/docker/1.13.1/87.git07f3374.el7/x86_64/docker-rhel-push-plugin-1.13.1-87.git07f3374.el7.x86_64.rpm

ssh -F ssh_config host yum -y install rh-python36-python-virtualenv origin-clients distgen \
              https://kojipkgs.fedoraproject.org//packages/source-to-image/1.1.7/3.fc29/x86_64/source-to-image-1.1.7-3.fc29.x86_64.rpm #source-to-image

# Copy sources
rsync -azP -e 'ssh -F ssh_config' $(pwd)/ host:sources
# prepare CentOS machine for working with docker
ssh -F ssh_config host 'cd sources && ./ci-scripts/jenkins_ci/prepare-centos-docker.sh'
# Prepare shared sources (build scripts)
ssh -F ssh_config host 'cd sources && git submodule update --init'
