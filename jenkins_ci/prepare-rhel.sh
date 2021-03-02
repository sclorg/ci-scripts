#!/bin/bash

# The script prepares RHEL 7 machine for testing SCL images
# it creates ssh_config file and ./cleanup.sh file
# It also copies sources into OpenStack Slave machine
set -ex

RESTAG=$1
rconnection="--connection http://10.0.149.99:49100/"

resalloc $rconnection ticket --tag $RESTAG > ticket
ticket=$(cat ticket)
host=$(resalloc $rconnection ticket-wait "$ticket")

cat > ssh_config << EOF
UserKnownHostsFile /dev/null
StrictHostKeyChecking no
User root
ConnectTimeout 10

Host host
  Hostname ${host}
  IdentityFile ~/.ssh/id_rsa_resalloc
EOF

# Create script for cleanup
cat > .cleanup.sh << EOF
#!/bin/bash
set -ex

resalloc $rconnection ticket-close "$ticket"
rm ticket ssh_config
EOF
chmod a+x .cleanup.sh

# Copy sources and prepare shared sources (build scripts)
git clone https://github.com/sclorg/ci-scripts.git $(pwd)/ci-scripts
rsync -azP -e 'ssh -F ssh_config' $(pwd)/ host:sources
ssh -F ssh_config host 'cd sources && git submodule update --init'
