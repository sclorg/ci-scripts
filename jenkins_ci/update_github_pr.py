# !/usr/bin/python
# -*- coding: utf-8 -*-
# Create a Github Gist (an alternative to pastebin) which will be linked to from Github
import json
import requests
import sys
import os

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--context", help="Which system is tested. rhel7, rhel8, centos7 or fedora."
)
parser.add_argument("--gituser", help="GitHub user organization")
parser.add_argument("--gitproject", help="GitHub project organization")
parser.add_argument("--git-commit", help="Git commit where the diff is POST")
args = parser.parse_args()

context = args.context
gituser = args.gituser
gitproject = args.gitproject
git_commit = args.git_commit

if not git_commit:
    print("ERROR: git_commit is missing.")
    sys.exit(1)

if not gituser:
    print("ERROR: gituser, like sclorg is not specified.")
    sys.exit(1)

if not gitproject:
    print("ERROR: gitproject, like s2i-nodejs-container is not specified.")
    sys.exit(1)

if not context:
    print(
        "ERROR: context is missing. Supported are 'rhel7', 'rhel8', 'fedora', 'centos7'."
    )
    sys.exit(1)

if "BUILD_URL" not in os.environ:
    print("ERROR: BUILD_URL does exist as environment variable.")
    sys.exit(1)

build_log = {
    "description": "Build started.",
    "public": False,
    "target_url": "{build_url}/consoleText".format(build_url=os.environ["BUILD_URL"]),
    "context": "SCLorg-CI for {context}".format(context=context),
    "state": "pending",
}

print(build_log)
req = requests.post(
    "https://api.github.com/repos/{gituser}/{gitproject}/statuses/{git_commit}".format(
        gituser=gituser, gitproject=gitproject, git_commit=git_commit
    ),
    data=json.dumps(build_log),
    auth=("rhscl-automation", os.environ["GITHUB_TOKEN"]),
)

sys.exit(0)
