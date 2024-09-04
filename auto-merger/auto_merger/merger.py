#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2024 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import json
import sys

from typing import List


from auto_merger import utils


class AutoMerger:
    repo_data: List = []

    def __init__(self, container_name: str):
        self.container_name = container_name

    def get_gh_pr_list(self):
        cmd = ["gh pr list -s open --json number,title,labels"]
        gh_repo_list = utils.run_command(cmd=cmd, return_output=True)
        self.repo_data = json.loads(gh_repo_list)

    def clone_repo(self):
        pass

    def merge_pull_request(self):
        pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: merger.py [container-name]")
        print('OUTPUT DIR is ".", if not specified otherwise')
        sys.exit(5)
    auto_merger = AutoMerger(container_name=sys.argv[1])
    auto_merger.get_gh_pr_list()
    auto_merger.merge_pull_request()
