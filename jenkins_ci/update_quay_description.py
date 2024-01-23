#!/usr/bin/env python3

# This script updates Quay image description

import os
import sys
import requests
from typing import Optional, List


def print_api_error(status_code: int) -> None:
    errors = {
        400: "Bad Request",
        401: "Session required",
        403: "Unauthorized access",
        404: "Not found"
    }
    if status_code not in errors.keys():
        print("Unknown API error")
    else:
        print(errors[status_code])


def load_readme(dir: str) -> Optional[str]:
    readme_path = os.path.join(dir, "README.md")
    if not os.path.exists(readme_path):
        print(f"Invalid path: {readme_path} does not exist")
        return None
    with open(readme_path) as readme:
        lines = readme.readlines()
        if len(lines) > 100:
            lines = shorten_readme(lines)
        return "".join(lines)


def escape_code_block(lines: List[str]) -> None:
    """
    Ensures that all markdown code blocks created by backticks (```) are correctly 
    closed, so that any lines added afterwards will be outside of a code block.
    Unclosed code blocks can occur after shortening readme.
    """
    backtick_count = 0
    for line in lines:
        if "```" in line:
            backtick_count += 1
    if backtick_count % 2 == 1:
        lines.append("...\n```")


def shorten_readme(readme_as_list: List[str]) -> List[str]:
    """
    Shorten readme if it is too long
    """
    readme_as_list = readme_as_list[:98]
    escape_code_block(readme_as_list) 
    readme_as_list.append("\n<br>\n")
    readme_as_list.append(f"Learn more at <https://github.com/sclorg/{github_repo}/blob//master/{context}/README.md>")
    return readme_as_list


def update_description(readme: str) -> bool:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "description": readme
    }
    r = requests.put(API_REQUEST_PATH, headers=headers, json=data)
    if r.status_code != 200:
        print_api_error(r.status_code)
        return False
    return True


if __name__ == "__main__":
    token = os.environ["QUAY_IMAGE_UPDATE_DESC"] # Quay token
    image_name = os.environ["IMAGE_NAME"] # Quay image name
    registry_namespace = os.environ["REGISTRY_NAMESPACE"] # Quay namespace
    context = os.environ["DOCKER_CONTEXT"] # Build Context
    github_repo = os.environ["GITHUB_REPO"] # Name of repo on github

    API_REQUEST_PATH = f"https://quay.io/api/v1/repository/{registry_namespace}/{image_name}"
    
    readme = load_readme(context)
    if readme is None:
        sys.exit(1)

    if not update_description(readme):
        sys.exit(1)
    print("Operation successful")
