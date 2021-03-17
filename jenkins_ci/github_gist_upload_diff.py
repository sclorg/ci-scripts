#!/usr/bin/python
# -*- coding: utf-8 -*-
# Create a Github Gist (an alternative to pastebin) which will be linked to from Github
import json
import requests
import sys
import os

commit_url = sys.argv[1]
gitproject = sys.argv[2]

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

req = requests.post(
    "https://api.github.com/gists",
    data=json.dumps(gist),
    auth=("rhscl-automation", os.environ["GITHUB_TOKEN"]),
)

api_res = json.loads(req.content)
# Save Gist URL to a file which will be read by environment variable injector
with open("diff_url.prop", "w") as f:
    f.write("DIFF_GIST_URL={0}".format(api_res["html_url"]) + "\n")
