#!/usr/bin/python
# -*- coding: utf-8 -*-
# Set status and url to github commit
import json
import requests
import os
import sys

git_commit = sys.argv[1]
gituser = sys.argv[2]
gitproject = sys.argv[3]

if git_commit == "":
    print("ERROR: git_commit as first parameter is not specified.")
    sys.exit(1)

if gituser == "":
    print("ERROR: gitproject, like sclorg is not specified.")
    sys.exit(1)

if gitproject == "":
    print("ERROR: gitproject, like s2i-nodejs-container is not specified.")
    sys.exit(1)


status = {
    "state": "success",
    "target_url": os.environ["DIFF_GIST_URL"],
    "description": "Generated diff.",
    "context": "diff",
}

html_url = "https://api.github.com/repos/{gituser}/{gitproject}/statuses/{git_commit}".format(
    gituser=gituser, gitproject=gitproject, git_commit=git_commit
)
req = requests.post(
    html_url,
    data=json.dumps(status),
    auth=("rhscl-automation", os.environ["GITHUB_TOKEN"]),
)

api_res = json.loads(req.content)
print(api_res)
