#!/usr/bin/python
# -*- coding: utf-8 -*-
# Create a Github Gist (an alternative to pastebin) which will be linked to from Github
import json
import requests
import sys
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--commit-url", help="Git commit where the diff is POST")
parser.add_argument("--gitproject", help="GitHub project organization")
args = parser.parse_args()

commit_url = args.commit_url
gitproject = args.gitproject

if not commit_url:
    print("ERROR: commit_url parameter is missing.")
    sys.exit(1)

if not gitproject:
    print("ERROR: gitproject paramater, like s2i-nodejs-container is not specified.")
    sys.exit(1)

if "BUILD_NUMBER" not in os.environ:
    print("ERROR: BUILD_NUMBER does exist as environment variable.")
    sys.exit(1)

diff = ""
with open("./diff", "r") as f:
    diff = f.read()

filename = "{gitproject}-#{build_number}.diff".format(
    gitproject=gitproject, build_number=os.environ["BUILD_NUMBER"]
)
gist = {
    "description": commit_url,
    "public": False,
    "files": {filename: {"content": diff}},
}

print(gist)
req = requests.post(
    "https://api.github.com/gists",
    data=json.dumps(gist),
    auth=("rhscl-automation", os.environ["GITHUB_TOKEN"]),
)

api_res = json.loads(req.content)
# Save Gist URL to a file which will be read by environment variable injector
with open("diff_url.prop", "w") as f:
    f.write("DIFF_GIST_URL={0}".format(api_res["html_url"]) + "\n")
