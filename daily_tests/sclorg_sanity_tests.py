#!/usr/bin/env python3
import os
import sys
import requests
import yaml
import urllib3
import smtplib
import argparse

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Dict, List
from shutil import rmtree
from git import Repo
from git.exc import GitCommandError

SCLORG_REPOS = [
    # Format is 'repo_name' and 'package_name'
    ("s2i-perl-container", "perl"),
    ("s2i-nodejs-container", "nodejs"),
    ("s2i-php-container", "php"),
    ("s2i-ruby-container", "ruby"),
    ("s2i-python-container", "python"),
    ("postgresql-container", "postgresql"),
    ("redis-container", "redis"),
    ("varnish-container", "varnish"),
    ("mysql-container", "mysql"),
    ("mariadb-container", "mariadb"),
    ("nginx-container", "nginx")
]


OS_HOSTS = [
    "fedora",
    "centos7",
    "c9s",
    "c8s",
    "rhel7",
    "rhel8",
    "rhel9"
]

# This is reference link to internal repository
EOL_GA_URL = "https://url.corp.redhat.com/application-streams-yaml"


class SclOrgSanityChecker(object):
    def __init__(self):
        self.tmp_path_dir: Path
        self.repo = ""
        self.app_stream: Dict = {}
        self.cwd = os.getcwd()
        self.tmp_path_repo: Path
        self.report_file: str = ""
        self.report_text_filename: str = ""
        self.args = self.parse_args()
        self.data_dict: Dict = {}

    def write_to_textfile(self, msg):
        print(msg)
        with open(self.report_file, "a") as fw:
            fw.write(msg)
            fw.write("\n")

    def create_tmp_dir(self):
        print("Create temporary directory for sanity checks.")
        tmp_dir = TemporaryDirectory(suffix="sanity_tests")
        self.tmp_path_dir = Path(tmp_dir.name)

    def download_and_load_lifecycle_file(self):
        urllib3.disable_warnings()
        response = requests.get(EOL_GA_URL, verify=False)
        self.app_stream = yaml.safe_load(response.content)

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="SanityChecker program go through all "
                        "https://github.com/sclorg container images and "
                        "detects if .exclude, .devel-repo are obsolete or missing."
        )

        return parser.parse_args()

    def prepare(self):
        self.create_tmp_dir()
        self.download_and_load_lifecycle_file()
        self.collect_data()

    def check_files(self, ver: str) -> List[str]:
        checked_files = []
        for os_ver in OS_HOSTS:
            exclude_file = self.tmp_path_repo / ver / f".exclude-{os_ver}"
            dockerfile = self.tmp_path_repo / ver / f"Dockerfile.{os_ver}"
            devel_file = self.tmp_path_repo / ver / f".devel-repo-{os_ver}"
            if exclude_file.exists():
                checked_files.append(f".exclude-{os_ver}")
            if dockerfile.exists():
                checked_files.append(f"Dockerfile.{os_ver}")
            if devel_file.exists():
                checked_files.append(f".devel-repo-{os_ver}")

        return checked_files

    def check_file_exists(self, ver: str, file: str):
        return [x for x in self.data_dict[self.repo][ver] if x.startswith(file)]

    def exclude_file_exists(self, ver: str, os_ver: str):
        return self.check_file_exists(ver=ver, file=f".exclude-{os_ver}")

    def dockerfile_exists(self, ver: str, os_ver: str):
        return self.check_file_exists(ver=ver, file=f"Dockerfile.{os_ver}")

    def devel_repo_exists(self, ver: str, os_ver: str):
        return self.check_file_exists(ver=ver, file=f".devel-repo-{os_ver}")

    def check_exclude_file_not_dockerfile(self, ver: str, os_ver: str):
        ret_val = True
        print(f"Check .exclude file for {ver}.")
        if self.exclude_file_exists(ver=ver, os_ver=os_ver) and not self.dockerfile_exists(ver=ver, os_ver=os_ver):
            self.write_to_textfile(
                f"For version {ver} .exclude-{os_ver} is present in {ver}"
                f"but Dockerfile.{os_ver} not."
            )
            self.write_to_textfile(f"Think about for removal .exclude-{os_ver}.")
            ret_val = False
        return ret_val

    def check_devel_repo_file(self, ver: str, os_ver: str):
        ret_val = True
        print(f"Check .devel_repo file for {ver}.")
        if self.devel_repo_exists(ver=ver, os_ver=os_ver) and self.dockerfile_exists(ver=ver, os_ver=os_ver):
            # TODO Check if .devel-repo file can not be removed
            self.write_to_textfile(
                f".devel-repo-{os_ver} is present in {ver} and Dockerfile.{os_ver}."
            )
            self.write_to_textfile(
                "Check if image is not already GA."
            )
            ret_val = False
        return ret_val

    def check_tested_version(self, ver: str, os_ver: str):
        ret_val = True
        print(f"Check .exclude and Dockerfile for ver {ver}")
        # from datetime import date
        # today = date.today()
        # ymd = today.strftime("%Y%m%d")
        if self.exclude_file_exists(ver=ver, os_ver=os_ver) and self.dockerfile_exists(ver=ver, os_ver=os_ver):
            # TODO Check if image can not be tested.
            # if os_ver.startswith("rhel"):
            #     pkg_dict = [x for x in self.app_stream["lifecycles"] if x["name"] == pkg_name]
            #     enddate = ""
            #     print(pkg_dict)
            #     for pkg in pkg_dict:
            #         if pkg["stream"] != ver:
            #             continue
            #         if enddate not in pkg_dict:
            #             continue
            #         print(pkg_dict)
            #         enddate = pkg_dict["enddate"]
            #         print(f"{ymd} and {enddate}")
            self.write_to_textfile(
                f"File .exclude-{os_ver} is present in and Dockerfile.{os_ver} as well. "
                f"The version {ver} is not tested."
            )
            self.write_to_textfile(
                f"Please think about usage '.devel-repo-{os_ver}' or check if image does not reach EOL."
            )
            ret_val = False
        return ret_val

    def get_all_supported_versions(self, repo_name: str):
        versions = []
        if not (self.tmp_path_repo / "Makefile").exists():
            print(f"Makefile for repository {repo_name} does not exist.")
            return versions
        with open(self.tmp_path_repo / "Makefile") as f:
            ver_row = [x for x in f.readlines() if x.startswith("VERSIONS")][0]
            ver_row = ver_row.split("=")[1].strip()
            return ver_row.split(" ")

    def clone_repository(self, repo_name: str):
        try:
            print(f"Cloning repository {repo_name}")
            repo = Repo.clone_from(f"https://github.com/sclorg/{repo_name}", to_path=self.tmp_path_dir / repo_name)
            return True
        except GitCommandError as ex:
            self.write_to_textfile(f"Cloning repo has failed {ex}")
            return False

    def collect_data(self):
        for repo, pkg_name in SCLORG_REPOS:
            if not self.clone_repository(repo_name=repo):
                continue
            self.tmp_path_repo = self.tmp_path_dir / repo
            os.chdir(self.tmp_path_repo)
            versions_to_check = self.get_all_supported_versions(repo_name=repo)

            for ver in versions_to_check:
                if repo not in self.data_dict:
                    self.data_dict[repo] = {}
                self.data_dict[repo][ver] = self.check_files(ver)
            os.chdir(self.cwd)
            rmtree(self.tmp_path_dir / repo)
        print(self.data_dict)

    def run_check(self):
        global_result_flag = True
        failed_repos = []
        for repo in self.data_dict:
            self.report_file = Path(os.getcwd()) / f"{repo}.log"
            self.repo = repo
            for ver in self.data_dict[repo]:
                sanity_ok = True
                self.write_to_textfile(f"--- {ver}:")
                for os_ver in OS_HOSTS:
                    if not self.check_exclude_file_not_dockerfile(ver, os_ver):
                        sanity_ok = False
                    if not self.check_devel_repo_file(ver, os_ver):
                        sanity_ok = False
                    if not self.check_tested_version(ver, os_ver):
                        sanity_ok = False
                if sanity_ok:
                    os.unlink(self.report_file)
                else:
                    if repo not in failed_repos:
                        failed_repos.append(repo)
                    global_result_flag = False
        self.send_email(failed_repos=failed_repos, result=global_result_flag)
        print(f"Report text file is located here {self.report_file}")
        rmtree(self.tmp_path_dir)

    def send_email(self, failed_repos, result: bool = False):
        print(failed_repos)
        if result:
            subject_msg = "SCLORG: sanity checker did not hit any issue in https://github/sclorg containers"
            message = f"SCLORG sanity checker did not hit any issues for {SCLORG_REPOS}"
        else:
            subject_msg = "SCLORG: sanity checker hit some issues in https://github/sclorg containers"
            message = f"SCLORG sanity checker hit some issues in these repositories:\n"
            message += "\n".join(failed_repos)
        send_from = "phracek@redhat.com"
        send_to = ["phracek@redhat.com", "pkubat@redhat.com", "hhorak@redhat.com", "zmiklank@redhat.com"]
        msg = MIMEMultipart()
        msg['From'] = send_from
        msg['To'] = send_to
        msg['Subject'] = subject_msg
        msg.attach(MIMEText(message))
        if not result:
            import glob
            log_files = glob.glob(f"{os.getcwd()}/*.log")
            for log in log_files:
                attach = MIMEApplication(open(log, 'r').read(), Name=os.path.basename(str(log)))
                attach.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(str(log))))
                msg.attach(attach)
        smtp = smtplib.SMTP("127.0.0.1")
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()


if __name__ == "__main__":
    sanity_checker = SclOrgSanityChecker()
    sanity_checker.prepare()
    sanity_checker.run_check()
    sys.exit(0)
