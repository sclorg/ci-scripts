# !/usr/bin/python
# -*- coding: utf-8 -*-
# Create a Github Gist (an alternative to pastebin) which will be linked to from Github
import json
import requests
import sys
import os

context = sys.argv[1]
gituser = sys.argv[2]
gitproject = sys.argv[3]
git_commit = sys.argv[4]

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
    auth=("rhscl-automation", os.environ["GITHUB_TOKEN"]),
)
