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

images = {"RHEL 7": "registry.redhat.io/rhscl/APP_NAME-APP_VERSION-rhel7:latest",
          "RHEL 8": "registry.redhat.io/rhel8/APP_NAME-APP_VERSION:latest",
          "RHEL 9": "registry.redhat.io/rhel9/APP_NAME-APP_VERSION:latest",
          "UBI 7": "registry.redhat.io/ubi7/APP_NAME-APP_VERSION:latest",
          "UBI 8": "registry.redhat.io/ubi8/APP_NAME-APP_VERSION:latest",
          "UBI 9": "registry.redhat.io/ubi9/APP_NAME-APP_VERSION:latest",
          "CentOS Stream 8": "quay.io/sclorg/APP_NAME-APP_VERSION-c8s:latest",
          "CentOS Stream 9": "quay.io/sclorg/APP_NAME-APP_VERSION-c9s:latest"}

abbreviations ={"RHEL 7": "el7",
                "RHEL 8": "el8",
                "RHEL 9": "el9",
                "UBI 7": "ubi7",
                "UBI 8": "ubi8",
                "UBI 9": "ubi9",
                "CentOS Stream 8": "el8",
                "CentOS Stream 9": "el9"}

latest_description = """

WARNING: By selecting this tag, your application will automatically update to use the latest version available on OpenShift, including major version updates.
"""
