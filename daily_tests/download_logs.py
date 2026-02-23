#!/usr/bin/env python3
import os
import time
import sys
import re
import argparse
import requests
import xmltodict
import urllib3

from datetime import date
from pathlib import Path

urllib3.disable_warnings()


CONTAINERS = [
    "httpd-container",
    "mariadb-container",
    "mysql-container",
    "nginx-container",
    "postgresql-container",
    "redis-container",
    "s2i-base-container",
    "s2i-nodejs-container",
    "s2i-perl-container",
    "s2i-php-container",
    "s2i-python-container",
    "s2i-ruby-container",
    "valkey-container",
    "varnish-container",
]

REPORTS_PUBLIC_URL = "https://artifacts.dev.testing-farm.io"
REPORTS_PRIVATE_URL = "https://artifacts.osci.redhat.com/testing-farm"
LOG_DIR = os.getenv("SHARED_DIR")


class TestingFarmLogDownloader:
    """
    Download logs from Testing Farm and store them in the log directory.
    """

    def __init__(self, log_file: str, target: str, test: str):
        """
        Initialize the TestingFarmLogDownloader class.
        """
        self.log_file: Path = Path(log_file)
        self.target: str = target
        self.test: str = test
        self.request_id: str = None
        self.xml_dict: dict = None
        self.date = date.today().strftime("%Y-%m-%d")
        self.data_dir_url_link: str = None
        self.log_dir: Path = (
            Path(LOG_DIR)
            / "daily_reports_dir"
            / self.date
            / f"{self.target}-{self.test}"
        )

    def get_request_id(self) -> bool:
        """
        Get the request ID from the log file.
        """
        with self.log_file.open() as f:
            lines = f.readlines()

        for line in lines:
            if "api https://api.dev.testing-farm.io/v0.1/requests/" in line:
                self.request_id = (
                    line.replace("api https://api.dev.testing-farm.io/v0.1/", "")
                    .split("/")[1]
                    .strip()
                )
                break

        if not self.request_id:
            print("Request ID not found in the log.")
            return False

        print(f"Request ID: {self.request_id}")
        return True

    def download_log(self, log_name_url: str, log_name: str = None) -> bool:
        """
        Download a log from the Testing Farm.
        """
        for _ in range(5):
            print(f"Downloading log: {log_name_url}")
            response = requests.get(log_name_url, verify=False)
            if response.status_code == 200:
                with (self.log_dir / log_name).open("wb") as f:
                    f.write(response.content)
                return True
            else:
                print(f"Failed to download log: {response.status_code}")
                time.sleep(3)  # Wait before retrying
        else:
            print("Failed to download log after multiple attempts.")
            return False

    def download_tmt_logs(self):
        """
        Download TMT logs from the Testing Farm.
        """
        if not self.xml_dict:
            print("XML report not found.")
            return False
        list_logs_to_download = ["tmt-verbose-log", "tmt-log"]
        for log in self.xml_dict["testsuites"]["testsuite"]["logs"]["log"]:
            if log["@name"] in list_logs_to_download:
                self.download_log(log["@href"], log["@name"])
                continue
            if log["@name"] == "data":
                self.data_dir_url_link = log["@href"]

    def get_list_of_containers_logs(self, html_content: str):
        """
        Get the list of failed containers from the HTML content.
        """
        try:
            list_of_failed_containers = []
            for line in html_content.split("\n"):
                if re.search(r"<a href=\"[a-zA-Z0-9.-]+\">", line):
                    list_of_failed_containers.append(
                        re.search(r"<a href=\"[a-zA-Z0-9.-]+\">", line).group(0)
                    )
            return list_of_failed_containers
        except Exception as e:
            print(f"Failed to get list of failed containers: {e}")
            return False

    def download_container_logs(self, failed: bool = False) -> bool:
        """
        Download the failed container logs from the Testing Farm.
        """
        if not self.data_dir_url_link:
            print("Data directory URL link not found.")
            return False
        url_link = self.data_dir_url_link
        if failed:
            url_link += "/results"

        print(f"Data directory URL link: {url_link}")
        response = requests.get(url_link, verify=False)
        if response.status_code == 200:
            print(response.text)
        else:
            print(f"Failed to download data/results directory: {response.status_code}")
            return False
        for cont in CONTAINERS:
            self.download_log(f"{url_link}/{cont}.log", f"{cont}.log")
        return True

    def get_xml_report(self) -> bool:
        """
        Get the XML report from the Testing Farm.
        """
        if self.target in ["fedora", "c9s", "c10s"]:
            xml_report_url = f"{REPORTS_PUBLIC_URL}/{self.request_id}/results.xml"
        else:
            xml_report_url = f"{REPORTS_PRIVATE_URL}/{self.request_id}/results.xml"
        print(f"XML Report URL: {xml_report_url}")
        for _ in range(5):
            response = requests.get(xml_report_url, verify=False)
            if response.status_code == 200:
                self.xml_dict = xmltodict.parse(response.content)
                break
            else:
                print(f"Failed to download XML report: {response.status_code}")
                time.sleep(3)  # Wait before retrying
        else:
            print("Failed to download XML report after multiple attempts.")
            return False
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download logs from Testing Farm.")
    parser.add_argument("log_file", type=str, help="Path to the log file")
    parser.add_argument("target", type=str, help="Target environment")
    parser.add_argument("test", type=str, help="Test name")

    args = parser.parse_args()

    downloader = TestingFarmLogDownloader(args.log_file, args.target, args.test)
    downloader.get_request_id()
    if not downloader.request_id:
        print("Cannot download logs without a valid request ID.")
        sys.exit(1)
    if not downloader.get_xml_report():
        print("Failed to download XML report.")
        sys.exit(1)
    downloader.download_tmt_logs()
    downloader.download_container_logs()
    downloader.download_container_logs(failed=True)
