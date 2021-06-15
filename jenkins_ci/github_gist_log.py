#!/usr/bin/python
# -*- coding: utf-8 -*-
# Create a Github Gist (an alternative to pastebin) which will be linked to from Github
import json
import requests
import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--context", help="Which system is tested. rhel7, rhel8, centos7 or fedora."
)
parser.add_argument("--gituser", help="GitHub user organization")
parser.add_argument("--gitproject", help="GitHub project organization")
parser.add_argument("--git-commit", help="Git commit where the diff is POST")
parser.add_argument(
    "--force", help="Downloading consoleText failed for network issues", type=bool
)
args = parser.parse_args()

context = args.context
gituser = args.gituser
gitproject = args.gitproject
git_commit = args.git_commit
force = args.force

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

if not force:
    with open(
        "build_log", "r"
    ) as f:  # Read the log of this build saved in a previous step
        build_log = f.read()

    with open("build_log.json", "r") as f_json:
        build_json = json.loads(f_json.read())

    print("Build gist")
    gist = {
        "description": git_commit,
        "public": False,
        "files": {
            "{gitproject}-#{build_number}.sh".format(
                gitproject=gitproject, build_number=os.environ["BUILD_NUMBER"]
            ): {"content": build_log}
        },
    }
    print("Send request to gist")
    req = requests.post(
        "https://api.github.com/gists",
        data=json.dumps(gist),
        auth=("rhscl-automation", os.environ["GITHUB_TOKEN"]),
    )

    api_res = json.loads(req.content)

    if "html_url" not in api_res:
        print("html_url is not present in api_res {api_res}".format(api_res=api_res))
        sys.exit(1)

if "result" in build_json and build_json["result"] == "SUCCESS":
    build_state = "success"
else:
    build_state = "failure"

print("update dist-git-url"
if not force:
    html_url = api_res["html_url"]
else:
    html_url = "{html_url}/consoleText".format(html_url=os.environ["BUILD_URL"])
dist_git_url = {
    "description": "Build finished",
    "public": False,
    "target_url": api_res["html_url"],
    "context": "SCLorg-CI for {context}".format(context=context),
    "state": build_state,
}

print("Post status of GitHub pull request")
req = requests.post(
    "https://api.github.com/repos/{gituser}/{gitproject}/statuses/{git_commit}".format(
        gituser=gituser, gitproject=gitproject, git_commit=git_commit
    ),
    data=json.dumps(dist_git_url),
    auth=("rhscl-automation", os.environ["GITHUB_TOKEN"]),
)
# Save Gist URL to a file which will be read by evironment variable injector
with open("build_log_url.prop", "w") as f:
    f.write("BUILD_GIST_URL=" + api_res["html_url"] + "\n")

sys.exit(0)
