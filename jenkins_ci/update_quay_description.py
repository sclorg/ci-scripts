#!/usr/bin/env python3

# This script updates Quay image description

import os
import sys
import re
import requests
from typing import Optional, List


def print_api_error(status_code: int) -> None:
    errors = {400: "Bad Request",
              401: "Session required",
              403: "Unauthorized access",
              404: "Not found"}
    if status_code not in errors.keys():
        print("Unknown API error")
    else:
        print(errors[status_code])


def load_readme_as_list(dir: str) -> Optional[List[str]]:
    readme_path = os.path.join(dir, "README.md")
    if not os.path.isfile(readme_path):
        print(f"Invalid path: {readme_path} does not exist")
        return None
    with open(readme_path) as readme:
        lines = readme.readlines()
        for i, line in enumerate(lines):
            if re.match("Description", line):
                if i + 3 >= len(lines):
                    break
                return lines[i + 3:]
    print("Invalid README format")
    return None


def escape_code_block(lines: List[str]):
    backtick_count = 0
    for line in lines:
        if "```" in line:
            backtick_count += 1
    if backtick_count % 2 == 1:
        lines.append("...\n```")
    return lines


def update_description(readme: str) -> int:
    api_request_path = f"https://quay.io/api/v1/repository/{registry_namespace}/{image_name}"
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {token}"}
    data = {"description": readme}
    r = requests.put(api_request_path, headers=headers, json=data)
    return r.status_code


if __name__ == "__main__":
    token = os.environ["REGISTRY_TOKEN"] # Quay token
    image_name = os.environ["IMAGE_NAME"] # Quay image name
    registry_namespace = os.environ["REGISTRY_NAMESPACE"] # Quay namespace
    context = os.environ["DOCKER_CONTEXT"] # Build Context
    github_repo = os.environ["GITHUB_REPO"] # Name of repo on github
    
    readme_as_list = load_readme_as_list(context)
    if readme_as_list is None:
        sys.exit(1)
    if len(readme_as_list) > 100:
        readme_as_list = readme_as_list[:98]
        escape_code_block(readme_as_list)
        readme_as_list.append("\n<br>\n")
        readme_as_list.append(f"Learn more at <https://github.com/sclorg/{github_repo}/blob//master/{context}/README.md>")
    
    readme = "".join(readme_as_list)
    request_status = update_description(readme)
    if request_status != 200:
        print_api_error(request_status)
        sys.exit(1)
    print("Operation successful")
