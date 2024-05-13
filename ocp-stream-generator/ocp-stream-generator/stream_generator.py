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


import yaml
import json
import sys
from distribution_data import abbreviations, images, latest_description

class YamlLoader:
    _data = None
    yaml_path = None

    def __init__(self, yaml):
        self.yaml_path = yaml

    @property
    def data(self):
        if not self._data:
            with open(self.yaml_path,"r") as file:
                self._data = yaml.safe_load(file)[0]
        return self._data


class ImagestreamFile:
    filename: str
    tags =  None
    latest_tag = None
    custom_tags = None
    app_name: str
    app_pretty_name: str
    is_correct = True

    # The mapping of stream names to distros is not 1 to 1.
    # For example stream name el8-16 can be RHEL8 or CentOS Stream 8 distro.
    # As the Latest tag is defined by the stream name only,
    # we need go through all tags in Image Stream File and return
    # a distro of a tag with the same stream name.
    def obtain_distro_for_latest(self, stream_name):
        for tag in self.tags:
            if tag.stream_name == stream_name:
                return tag.distro_name
        print("The stream name of the latest tag was not found in the rest of tags")
        self.is_correct = False


    def __init__(self, file, header):
        self.app_name = header["name"]
        self.app_pretty_name = header["pretty_name"]
        self.filename = file["filename"]
        # hack - UBI images are both in public and private repos, need to
        # distinguish between them based on filename
        repo_access = "public" if "centos" in self.filename else "private"
        self.tags = []
        for distro in file["distros"]:
            for app_version in distro["app_versions"]:
                _tag = Tag(header, distro["name"], repo_access, app_version)
                self.tags.append(_tag)
        _latest_distro = self.obtain_distro_for_latest(file["latest"]);
        if not _latest_distro:
            return
        self.latest_tag = LatestTag(header, _latest_distro, repo_access, file["latest"])
        self.custom_tags = []
        if "custom_tags" in file:
            for custom_tag in file["custom_tags"]:
                _tag = CustomTag(header, repo_access, custom_tag)
                self.custom_tags.append(_tag)

class Tag:
    stream_name: str
    app_version: int
    distro_name: str
    image: str
    description: str
    sample_repo = None
    app_name: str
    app_pretty_name: str
    category: str
    repo_access = None
    kind: str

    def obtain_stream_name(self):
        return f"{str(self.app_version)}-{abbreviations[self.distro_name]}"

    def obtain_image(self):
        return images[self.distro_name][self.repo_access] \
            .replace("APP_VERSION", str(self.app_version).replace(".","")) \
            .replace("APP_NAME", self.app_name)

    def obtain_description(self, header):
        return header["description"] \
            .replace("APP_VERSION", str(self.app_version)) \
            .replace("DISTRO_NAME", self.distro_name)

    def obtain_display_name(self):
        return f"{self.app_pretty_name} {str(self.app_version)} ({self.distro_name})"

    def __init__(self, header, distro_name, repo_access, app_version):
        self.repo_access = repo_access
        self.category = header["category"]
        self.app_name = header["name"]
        self.app_pretty_name = header["pretty_name"]
        self.sample_repo = header["sample_repo"]
        self.app_version = app_version
        self.distro_name = distro_name
        self.description = self.obtain_description(header)
        self.image = self.obtain_image()
        self.stream_name = self.obtain_stream_name()
        self.kind = "DockerImage"
        self.display_name = self.obtain_display_name()


class CustomTag(Tag):
    def __init__(self, header, repo_access, custom_tag):
        self.app_version = custom_tag["app_version"]
        self.stream_name = custom_tag["name"]
        self.distro_name = custom_tag["distro"]
        self.description = self.obtain_description(header)
        self.kind = "DockerImage"

        self.repo_access = repo_access
        self.category = header["category"]
        self.app_name = header["name"]
        self.app_pretty_name = header["pretty_name"]
        self.sample_repo = header["sample_repo"]
        self.description = self.obtain_description(header)
        self.image = self.obtain_image()
        self.display_name = self.obtain_display_name()

class LatestTag(Tag):
    def obtain_description(self, header):
        return super().obtain_description(header) + latest_description

    def __init__(self, header, distro_name, repo_access, stream_name):
        self.app_version = stream_name.split("-",1)[0]
        # the stream name (e.g., 12-el8) is used in image field in latest tag
        self.image = stream_name
        self.stream_name = "latest"
        self.distro_name = distro_name
        self.description = self.obtain_description(header)
        self.kind = "ImageStreamTag"
        self.repo_access = repo_access
        self.category = header["category"]
        self.app_name = header["name"]
        self.app_pretty_name = header["pretty_name"]
        self.display_name = f"{self.app_pretty_name} {str(self.app_version)} (Latest)"
        self.sample_repo = header["sample_repo"]


class JsonBuilder:
    def create_header(self, data):
        _header = {}
        _header["kind"] = "ImageStream"
        _header["apiVersion"] = "image.openshift.io/v1"
        _header["metadata"] =  {
                                 "name": data.app_name,
                                 "annotations": {
                                    "openshift.io/display-name": data.app_pretty_name
                                 }
                               }
        _header["spec"] = {"tags": []}
        return _header

    def create_annotation(self, tag):
        _ann = {}
        _ann["openshift.io/display-name"] = tag.display_name
        _ann["openshift.io/provider-display-name"] =  "Red Hat, Inc."
        _ann["description"] = tag.description
        _ann["iconClass"] = f"icon-{tag.app_name}"
        _ann["tags"] = f"{tag.category},{tag.app_name}"
        _ann["version"] = str(tag.app_version)
        if tag.sample_repo != "":
            _ann["sampleRepo"] = tag.sample_repo
        return _ann


    def add_tag(self, _json, tag):
        _tag = {}
        _tag["name"] = tag.stream_name
        _tag["annotations"] = self.create_annotation(tag)
        _tag["from"] = {"kind": tag.kind, "name": tag.image}
        _tag["referencePolicy"] = {"type": "Local"}
        _json["spec"]["tags"].append(_tag)
        return _json

    def generate_json(self, isf_data):
        _json = {}
        _json = self.create_header(isf_data)
        for tag in isf_data.tags:
            _json = self.add_tag(_json, tag)
        for tag in isf_data.custom_tags:
            _json = self.add_tag(_json, tag)
        self.add_tag(_json, isf_data.latest_tag)
        return json.dumps(_json, indent=2)

def main():
    if len(sys.argv) != 2:
        print("please provide YAML conf file as first parameter of this script")
        return 5
    yaml_loader = YamlLoader(sys.argv[1])
    builder = JsonBuilder()

    isf_header = yaml_loader.data
    is_files = isf_header.pop("imagestream_files")
    for isf in is_files:
        isf_data = ImagestreamFile(isf, isf_header)
        if not isf_data.is_correct:
            return 5
        with open(isf_data.filename, "w") as json_file:
            json_file.write(builder.generate_json(isf_data)+ "\n")

if __name__ == "__main__":
    main();

