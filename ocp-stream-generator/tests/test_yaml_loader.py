#!/usr/bin/env python3

import pytest
import sys

from stream_generator import YamlLoader

def test_load_yaml():
    loader = YamlLoader("tests/data/minimal.yml")
    result = {'name': 'test_pkg', 'pretty_name': 'Test Package', 'sample_repo': '', 'category': 'testing', 'description': "Let's test this!", 'imagestream_files': [{'filename': 'test-centos.json', 'latest': '2-el9', 'distros': [{'name': 'CentOS Stream 8', 'app_versions': [2, 3, 1]}, {'name': 'CentOS Stream 9', 'app_versions': [2]}]}]}
    assert loader.json_data == result
