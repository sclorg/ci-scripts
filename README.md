# ci-scripts
Set of generic scripts that are run in the CI (Jenkins or any other)

## daily_tests

The directory contains a script for running SCL
tests which are executed periodically each day.

The aim of this script is to avoid the situation
if an upstream, like `gunicorn` updates PyPi
version and our python container tests are failing.

## jenkins_ci scripts

The directory contains the set of scripts used by our Jenkins CI.
Each script has a documentation inside.

### Scripts used for tests

Scripts which prepares OpenStack instance and running tests
* add-dependencies-remote.sh - used by [add_dependencies_remote.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/add_dependencies_remote.yaml)
  for testing containers by PR `[test]`
* commit-into-generated-branch.sh - used by [image-test.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/image-test.yaml)
  for testing containers by PR `[test]`. Commits sources ito generated branch
* image-test-openshift.sh - used by [image-test-openshift.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/image-test-openshift.yaml)
  for testing containers in OpenShift 3 environment by PR comment `[test-openshift]`
* image-test-openshift-4.sh - used by [image-test-openshift-4.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/image-test-openshift-4.yaml)
  for testing containers in OpenShift 4 environment by PR comment `[test-openschit-4]`
* prepare-centos.sh - [prepare-centos.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/prepare-centos.yaml)
  for testing container in CentOS by PR `[test] | [test-openshift]`
* prepare-centos-docker.sh - used by [prepare-centos.sh](https://github.com/sclorg/ci-scripts/jenkins_ci/prepare-centos.sh)
  for testing container in CentOS. It installs docker environment
* prepare-rhel.sh - used by [prepare-rhel.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/prepare-rhel.yaml)
  for testing container in RHEL by PR `[test] | [test-openshift] | [test-openshift-4]`
* run-tests.sh - used by [image-test.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/image-test.yaml)
  for testing containers by PR comment `[test]`
* run-container-common-scripts.sh - used by [container-common-scripts-test.yaml](https://github.com/sclorg/rhscl-container-ci/blob/master/yaml/jobs/misc/container-common-scripts-test.yaml) for testing container-common-scripts by PR comment `[test]`

Scripts which updates PR informaction
* jenkins_diff.sh - used by [upload-diff.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/publishers/upload-diff.yaml)
  for uploading diff between generated branches into GitHub Gist
* jenkins_upload_log.sh - used by [upload-log.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/publishers/upload-log.yaml)
  for uploading testing log into GitHub Gist
* update_github_pr.sh - used by [update_github_pr.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/update_github_pr.yaml)
  for testing containers by PR `[test]`


### Scripts used for building and pushing changes into Quay.io

* push-into-generated-branch.sh - used by [image-build-push.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/image-build-push.yaml)
  for building containers and pushing into Quay.io
* tag-push-to-registry.sh - used by [image-build-push.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/image-build-push.yaml)
  for building containers and pushing into Quay.io
* upload_quay.sh - used by [quay-hub-update.yaml](https://github.com/sclorg/rhscl-container-ci/yaml/builders/quay-hub-update.yaml)
  for updating description in Quay.io
