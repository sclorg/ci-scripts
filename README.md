# ci-scripts
Set of generic scripts that are run in the CI (Jenkins or any other)

## daily_tests

The directory contains a script for running SCL
tests which are executed periodically each day.

The aim of this script is to avoid the situation
if an upstream, like `gunicorn` updates PyPi
version and our python container tests are failing.