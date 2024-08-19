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

images = {
    "RHEL 8": {"private": "registry.redhat.io/rhel8/APP_NAME-APP_VERSION:latest"},
    "RHEL 9": {"private": "registry.redhat.io/rhel9/APP_NAME-APP_VERSION:latest"},
    "UBI 8": {
        "private": "registry.redhat.io/ubi8/APP_NAME-APP_VERSION:latest",
        "public": "registry.access.redhat.com/ubi8/APP_NAME-APP_VERSION:latest",
    },
    "UBI 9": {
        "private": "registry.redhat.io/ubi9/APP_NAME-APP_VERSION:latest",
        "public": "registry.access.redhat.com/ubi9/APP_NAME-APP_VERSION:latest",
    },
    "UBI 10": {
        "private": "registry.redhat.io/ubi10/APP_NAME-APP_VERSION:latest",
        "public": "registry.access.redhat.com/ubi10/APP_NAME-APP_VERSION:latest",
    },
    "CentOS Stream 8": {"public": "quay.io/sclorg/APP_NAME-APP_VERSION-c8s:latest"},
    "CentOS Stream 9": {"public": "quay.io/sclorg/APP_NAME-APP_VERSION-c9s:latest"},
    "CentOS Stream 10": {"public": "quay.io/sclorg/APP_NAME-APP_VERSION-c10s:latest"},
}

abbreviations = {
    "RHEL 8": "el8",
    "RHEL 9": "el9",
    "RHEL 10": "el10",
    "UBI 8": "ubi8",
    "UBI 9": "ubi9",
    "UBI 10": "ubi10",
    "CentOS Stream 8": "el8",
    "CentOS Stream 9": "el9",
    "CentOS Stream 10": "el10",
}

latest_description = (
    "\n\nWARNING: By selecting this tag,"
    " your application will automatically"
    " update to use the latest version available on OpenShift,"
    " including major version updates.\n"
)
