#!/usr/bin/python
# -*- coding: utf-8 -*-
# Set status and url to github commit
import json
import requests
import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--git-commit", help="Git commit where the diff is POST")
parser.add_argument("--gituser", help="GitHub user organization")
parser.add_argument("--gitproject", help="GitHub project organization")
args = parser.parse_args()

git_commit = args.git_commit
gituser = args.gituser
gitproject = args.gitproject

if not git_commit:
    print("ERROR: git_commit as first parameter is not specified.")
    sys.exit(1)

if not gituser:
    print("ERROR: gitproject, like sclorg is not specified.")
    sys.exit(1)

if not gitproject:
    print("ERROR: gitproject, like s2i-nodejs-container is not specified.")
    sys.exit(1)

status = {
    "state": "success",
    "target_url": os.environ["DIFF_GIST_URL"],
    "description": "Generated diff.",
    "context": "diff",
}

print(status)
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
