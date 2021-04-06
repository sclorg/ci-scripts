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

# Copy sources and prepare shared sources (build scripts)
rsync -azP -e 'ssh -F ssh_config' $(pwd)/ host:sources
ssh -F ssh_config host 'cd sources && git submodule update --init'
# prepare CentOS machine for working with docker
ssh -F ssh_config host 'cd sources && ./ci-scripts/jenkins_ci/prepare-centos-docker.sh'
