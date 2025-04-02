#!/bin/bash

set -x

/usr/local/bin/pbincli send --server https://privatebin.corp.redhat.com --expire 1month --no-insecure-warning --no-check-certificate --format plaintext < $1 > $2 2>&1
