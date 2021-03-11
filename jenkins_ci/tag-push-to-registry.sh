#!/bin/bash

# Script taggedin build images and pushes them into Quay.io and later on into Docker.io registry.
# Parameters:
# First parameter - TARGET_OS
# Second parameter - HUB_NAMESPACE
#            taken from https://github.com/sclorg/rhscl-container-ci/yaml/jobs/collections/*.yaml
#            defined in .project.jobs.'{job_prefix}-{name}-build'
set -ex

TARGET_OS="$1"
HUB_NAMESPACE="$2"

if [ x"${TARGET_OS}" == "x" ]; then
  echo "1st parameter as TARGET_OS for tag-push-to-registry.sh script has to be specified."
  exit 1
fi

if [ x"${HUB_NAMESPACE}" == "x" ]; then
  echo "2nd parameter as HUB_NAMESPACE for tag-push-to-registry.sh script has to be specified."
  exit 1
fi

make tag TARGET="${TARGET_OS}" | tee output

image_ids=$(cat output | grep -- '-> Tagging image' | cut -d' ' -f 4 | sed "s/'//g")
for image_id in $image_ids; do
    image_tags+=$(docker image inspect "$image_id" --format '{{range $i, $tag := .RepoTags}}{{$tag}} {{end}}')
done

# All images are built in format quay.io/centos7/<image_name>
# image_tags looks like:
# quay.io/centos7/python-38-centos7:1 quay.io/centos7/python-38-centos7:20201125-f9402d2 quay.io/centos7/python-38-centos7:latest quay.io/centos7/python-38-centos7:raw
for image in $image_tags; do
  case $image in
    *:raw|*:squashed) continue ;;
  esac

  # By default images are now tagged into localhost/ registry
  # Image name for Docker Hub
  # hub_namespace is docker.io/centos and we need to get from image only image name
  image_name={HUB_NAMESPACE}/${image##*/}
  echo "Push ${image} into Quay Hub"
  HOME=~/.docker_credentials/quay_io docker push "${image}"
  echo "Push ${image_name} into Docker Hub"
  docker tag "${image}" "${image_name}"
  HOME=~/.docker_credentials/docker_io docker push "${image_name}"
done
rm output
