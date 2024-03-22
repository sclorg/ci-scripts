#!/usr/bin/env python3

import pytest
import sys
import re
from stream_generator import JsonBuilder
from stream_generator import Tag
from stream_generator import ImagestreamFile
from data.data_json_builder import add_tag_result
from data.data_json_builder import add_tag_latest_result
from data.data_json_builder import create_annotation_result
from data.data_json_builder import create_annotation_latest_result
from data.data_json_builder import create_header_result
from data.data_json_builder import generate_json_result
builder = JsonBuilder()

header = {"name": "test", "pretty_name": "Test", "sample_repo": "", "category": "test", "description": "test description"}



def test_add_tag():
    tag = Tag(header, "RHEL 8", "private", version=1)
    assert builder.add_tag({"spec": { "tags": []}}, tag)  ==  add_tag_result

def test_add_latest_tag():
    tag_latest = Tag(header, "RHEL8", "private", latest="1-el8")
    assert builder.add_tag({"spec": { "tags": []}}, tag_latest)  ==  add_tag_latest_result

def test_create_annotation():
    tag = Tag(header, "RHEL 8", "private", version=1)
    assert builder.create_annotation(tag) == create_annotation_result

def test_create_annotation_latest():
    latest_tag = Tag(header, "RHEL 8", "private", latest="1-el8")
    assert builder.create_annotation(latest_tag) == create_annotation_latest_result

def test_create_header():
    header = {"name": "test", "pretty_name": "Test", "category": "test", \
              "sample_repo": "", "description": "test description"}
    file = {"filename": "test-file.json", "distros": \
           [{"name": "RHEL 8", "app_versions": [1]}], "latest": "1-el8"}
    isf_data = ImagestreamFile(file, header)
    assert builder.create_header(isf_data) == create_header_result

def test_generate_json():
    header = {"name": "test", "pretty_name": "Test", "category": "test", \
              "sample_repo": "", "description": "test description"}
    file = {"filename": "test-file.json", "distros": \
           [{"name": "RHEL 8", "app_versions": [1]}], "latest": "1-el8"}
    isf_data = ImagestreamFile(file, header)
    stripped_json= re.sub(r"[\n\t\s\\n]*", "", builder.generate_json(isf_data))
    stripped_result=re.sub(r"[\n\t\s\\n]*", "", generate_json_result)
    assert stripped_json == stripped_result
