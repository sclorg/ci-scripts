# !/usr/bin/python
# -*- coding: utf-8 -*-
# Create a Github Gist (an alternative to pastebin) which will be linked to from Github
import json
import requests
import sys
import os
import subprocess

context = sys.argv[1]
gituser = sys.argv[2]
gitproject = sys.argv[3]

ci_message = json.loads(os.environ["CI_MESSAGE"])
pull_number = ci_message["issue"]["number"]

git_fetch = subprocess.check_output(
    ["git", "fetch", "origin", "+refs/pull/*:refs/remotes/origin/pr/*"], shell=True
)
print(git_fetch)
git_checkout = subprocess.check_output(
    ["git", "checkout", "origin/pr/{pull_number}/head".format(pull_number=pull_number)],
    shell=True,
)
print(git_checkout)
git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], shell=True)
print(git_commit)

build_log = {
    "description": "Build started.",
    "public": False,
    "target_url": "$BUILD_URL/consoleText",
    "context": "Jenkins-CI for {context}".format(context=context),
    "state": "pending",
}

req = requests.post(
    "https://api.github.com/repos/{gituser}/{gitproject}/statuses/{git_commit}".format(
        gituser=gituser, gitproject=gitproject, git_commit=git_commit
    ),
    data=json.dumps(build_log),
    auth=("$GITHUB_USERNAME", "$GITHUB_TOKEN"),
)
