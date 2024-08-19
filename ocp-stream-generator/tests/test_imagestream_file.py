#!/usr/bin/env python3


from stream_generator import ImagestreamFile


def test_create_isf():
    isf = {
        "filename": "test-centos.json",
        "latest": "2-el9",
        "distros": [
            {"name": "CentOS Stream 8", "app_versions": [2, 3, 1]},
            {"name": "CentOS Stream 9", "app_versions": [2]},
        ],
    }
    isf_header = {
        "name": "test_pkg",
        "pretty_name": "Test Package",
        "sample_repo": "",
        "category": "testing",
        "description": "Let's test this!",
    }
    isf_data = ImagestreamFile(isf, isf_header)
    assert isf_data.latest_tag.stream_name == "latest"
    assert isf_data.latest_tag.image == "2-el9"
    assert isf_data.app_pretty_name == "Test Package"
    assert isf_data.app_name == "test_pkg"
    assert isf_data.latest_tag.distro_name == "CentOS Stream 9"
    assert isf_data.tags[0].description == "Let's test this!"


def test_create_isf_custom_tags():
    isf = {
        "filename": "test-centos.json",
        "custom_tags": [
            {"name": "my custom tag", "app_version": "11", "distro": "UBI 8"}
        ],
        "latest": "2-el9",
        "distros": [
            {"name": "CentOS Stream 8", "app_versions": [2, 3, 1]},
            {"name": "CentOS Stream 9", "app_versions": [2]},
        ],
    }
    isf_header = {
        "name": "test_pkg",
        "pretty_name": "Test Package",
        "sample_repo": "",
        "category": "testing",
        "description": "Let's test this!",
    }
    isf_data = ImagestreamFile(isf, isf_header)
    print(isf_data.tags)
    assert isf_data.latest_tag.stream_name == "latest"
    assert isf_data.latest_tag.image == "2-el9"
    assert isf_data.app_pretty_name == "Test Package"
    assert isf_data.app_name == "test_pkg"
    assert isf_data.latest_tag.distro_name == "CentOS Stream 9"
    assert isf_data.tags[0].description == "Let's test this!"
    assert isf_data.custom_tags[0].stream_name == "my custom tag"
    assert isf_data.custom_tags[0].distro_name == "UBI 8"
