#!/usr/bin/env python3

import pytest
import sys
import re
from stream_generator import JsonBuilder
from stream_generator import Tag
from stream_generator import ImagestreamFile
from data.data_json_builder import result_json
builder = JsonBuilder()

header = {"name": "test", "pretty_name": "Test", "sample_repo": "", "category": "test", "description": "test description"}



def test_add_tag():
    tag = Tag(header, "RHEL 8", version=1)
    result = {"spec": {"tags": [{"name": "1-el8", "annotations": {"openshift.io/display-name": "Test 1 (RHEL 8)", "openshift.io/provider-display-name": "Red Hat, Inc.", "description": "test description", "iconClass": "icon-test", "tags": "test,test", "version": "1"}, "from": {"kind": "DockerImage", "name": "registry.redhat.io/rhel8/test-1:latest"}, "referencePolicy": {"type": "Local"}}]}}
    assert builder.add_tag({"spec": { "tags": []}}, tag)  ==  result

def test_add_latest_tag():
    tag_latest = Tag(header, "RHEL8", latest="1-el8")
    result_latest = {"spec": {"tags": [{"name": "latest", "annotations": {"openshift.io/display-name": "Test 1 (Latest)", "openshift.io/provider-display-name": "Red Hat, Inc.", "description": "test description\n\nWARNING: By selecting this tag, your application will automatically update to use the latest version available on OpenShift, including major version updates.\n", "iconClass": "icon-test", "tags": "test,test", "version": "1"}, "from": {"kind": "ImageStreamTag", "name": "1-el8"}, "referencePolicy": {"type": "Local"}}]}}
    assert builder.add_tag({"spec": { "tags": []}}, tag_latest)  ==  result_latest

def test_create_annotation():
    tag = Tag(header, "RHEL 8", version=1)
    result = {"openshift.io/display-name": "Test 1 (RHEL 8)", "openshift.io/provider-display-name": "Red Hat, Inc.", "description": "test description", "iconClass": "icon-test", "tags": "test,test", "version": "1"}
    assert builder.create_annotation(tag) == result

def test_create_annotation_latest():
    latest_tag = Tag(header, "RHEL 8", latest="1-el8")
    latest_result = {"openshift.io/display-name": "Test 1 (Latest)", "openshift.io/provider-display-name": "Red Hat, Inc.", "description": "test description\n\nWARNING: By selecting this tag, your application will automatically update to use the latest version available on OpenShift, including major version updates.\n", "iconClass": "icon-test", "tags": "test,test", "version": "1"}
    assert builder.create_annotation(latest_tag) == latest_result

def test_create_header():
    header = {"name": "test", "pretty_name": "Test", "category": "test", \
              "sample_repo": "", "description": "test description"}
    file = {"filename": "test-file.json", "distros": \
           [{"name": "RHEL 8", "app_versions": [1]}], "latest": "1-el8"}
    isf_data = ImagestreamFile(file, header)
    result = {"kind": "ImageStream", "apiVersion": "image.openshift.io/v1", "metadata": {"name": "test", "annotations": {"openshift.io/display-name": "Test"}}, "spec": {"tags": []}}
    assert builder.create_header(isf_data) == result

def test_generate_json():
    header = {"name": "test", "pretty_name": "Test", "category": "test", \
              "sample_repo": "", "description": "test description"}
    file = {"filename": "test-file.json", "distros": \
           [{"name": "RHEL 8", "app_versions": [1]}], "latest": "1-el8"}
    isf_data = ImagestreamFile(file, header)
    stripped_json= re.sub(r"[\n\t\s\\n]*", "", builder.generate_json(isf_data))
    stripped_result=re.sub(r"[\n\t\s\\n]*", "", result_json)
    assert stripped_json == stripped_result
