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

SCLORG_REPOS = {
    # Format is 'repo_name' and 'package_name'
    "s2i-perl-container": "perl",
    "s2i-nodejs-container": "nodejs",
    "s2i-php-container": "php",
    "s2i-ruby-container": "ruby",
    "s2i-python-container": "python",
    "postgresql-container": "postgresql",
    "redis-container": "redis",
    "varnish-container": "varnish",
    "mysql-container": "mysql",
    "mariadb-container": "mariadb",
    "nginx-container": "nginx"
}


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
        self.pkg_name = ""
        self.app_stream: Dict = {}
        self.cwd = os.getcwd()
        self.tmp_path_repo: Path
        self.report_text_filename: str = ""
        self.args = self.parse_args()
        self.data_dict: Dict = {}
        self.failed_repos: List[str] = []
        self.global_result_flag: bool = True
        self.log_dir = os.getcwd()
        self.message = ""

    def update_message(self, msg):
        self.message += f"{msg}" + "\n"

    def write_to_textfile(self, msg, report_file):
        print(msg)
        with open(report_file, "a") as fw:
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
            description="GitHubSanityChecker program go through all "
                        "https://github.com/sclorg container images and "
                        "detects if .exclude, .devel-repo are obsolete or missing."
                        "The output logs are stored in current working directory."
        )
        parser.add_argument(
            "--send-email", action="store_true", help="The logs are send over SMTP mail.", default=False
        )
        parser.add_argument("--log-dir", help="The logs are stored in user defined directory")

        return parser.parse_args()

    def prepare(self) -> bool:
        if self.args.log_dir:
            if not os.path.exists(self.args.log_dir):
                print("Log dir you specified by --log-dir parameter does not exist.")
                return False
            self.log_dir = self.args.log_dir
        self.create_tmp_dir()
        self.download_and_load_lifecycle_file()
        self.collect_data()
        return True

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
        if self.exclude_file_exists(ver=ver, os_ver=os_ver) and not self.dockerfile_exists(ver=ver, os_ver=os_ver):
            self.update_message(
                f"For version {ver} .exclude-{os_ver} is present "
                f"but Dockerfile.{os_ver} not."
            )
            self.update_message(f"Think about for removal .exclude-{os_ver}.")
            ret_val = False
        if not ret_val:
            print(f"Check .exclude file and not Dockerfile hit some issue for {ver} in repo {self.repo}.")
        return ret_val

    def check_devel_repo_file(self, ver: str, os_ver: str):
        ret_val = True
        if self.devel_repo_exists(ver=ver, os_ver=os_ver) and self.dockerfile_exists(ver=ver, os_ver=os_ver):
            # TODO Check if .devel-repo file can not be removed
            self.update_message(
                f".devel-repo-{os_ver} is present in {ver} and Dockerfile.{os_ver}."
            )
            self.update_message(
                "Check if image is not already GA."
            )
            ret_val = False
        if not ret_val:
            print(f"Check for .devel-repo and Dockerfile hit some issue for {ver} in repo {self.repo}.")
        return ret_val

    def is_eol_version(self, ver: str, os_ver: str) -> int:
        from datetime import datetime
        today = datetime.today().date()
        pkg_dict = [x for x in self.app_stream["lifecycles"] if x["name"] == self.pkg_name]
        print(f"OS is {os_ver} and version is {ver}")
        for pkg in pkg_dict:
            if pkg["stream"] != ver:
                continue
            if "enddate" not in pkg:
                continue
            # Get RHEL version without 'rhel' prefix
            rhel_version = os_ver.lstrip("rhel")
            if not pkg["initial_product_version"].startswith(rhel_version):
                continue
            print(pkg)
            enddate = datetime.strptime(pkg["enddate"], "%Y%m%d").date()
            print(f"{today} and {enddate}")
            days_to_eol = (enddate - today).days
            print(f"Count of days till EOL {days_to_eol}")
            # Already reached EOL.
            if days_to_eol < 0:
                return 1
            # Less then 30 days to EOL.
            if days_to_eol < int(30):
                return 2
            else:
                return 0

    def check_tested_version(self, ver: str, os_ver: str):
        ret_val = True
        eol_flag = -1
        if self.exclude_file_exists(ver=ver, os_ver=os_ver) and self.dockerfile_exists(ver=ver, os_ver=os_ver):
            if os_ver.startswith("rhel"):
                eol_flag = self.is_eol_version(ver=ver, os_ver=os_ver)
            if eol_flag == 1:
                self.update_message(
                    f"File .exclude-{os_ver} is present and Dockerfile.{os_ver} as well. "
                    f"The version {ver} is not tested because it reached EOL already."
                )
                ret_val = True
            if eol_flag == 0:
                self.update_message(f"File .exclude-{os_ver} is present and Dockerfile.{os_ver} as well."
                                    f"The version {ver} does not reached EOL yet.")
                ret_val = True
            if eol_flag == 2:
                self.update_message("The image will reach EOL during next 30 days.")
                ret_val = False
        if not ret_val:
            print(f"Check for .exclude and Dockerfile hit some issue for {ver} in repo {self.repo}.")
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
        for repo, pkg_name in SCLORG_REPOS.items():
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
        for repo in self.data_dict:
            report_file = Path(self.log_dir) / f"{repo}.log"
            self.repo = repo
            self.pkg_name = SCLORG_REPOS[repo]
            sanity_ok = True
            for ver in self.data_dict[repo]:
                self.message = f"--- repo: {self.repo} and version: {ver}:\n"
                checker = True
                for os_ver in OS_HOSTS:
                    if not self.check_exclude_file_not_dockerfile(ver, os_ver):
                        checker = False
                    if not self.check_devel_repo_file(ver, os_ver):
                        checker = False
                    if not self.check_tested_version(ver, os_ver):
                        checker = False
                if not checker:
                    self.write_to_textfile(msg=self.message, report_file=report_file)
                    sanity_ok = False
            if sanity_ok:
                if Path(report_file).exists():
                    os.unlink(report_file)
            else:
                if repo not in self.failed_repos:
                    self.failed_repos.append(repo)
                self.global_result_flag = False
        print(f"Report text files are located here {self.log_dir}")
        rmtree(self.tmp_path_dir)

    def send_email(self):
        if not self.args.send_email:
            print("Sending email is not allowed")
            return
        if self.global_result_flag:
            subject_msg = "SCLORG: sanity checker did not hit any issue in https://github/sclorg containers"
            message = f"SCLORG sanity checker did not hit any issues for https://github/sclorg containers."
        else:
            subject_msg = "SCLORG: sanity checker hit some issues in https://github/sclorg containers"
            message = f"SCLORG sanity checker hit some issues in these repositories:\n"
            message += "\n".join(self.failed_repos)
        message += "\nIn case the information is wrong, please reach out " \
                   "phracek@redhat.com, pkubat@redhat.com or hhorak@redhat.com.\n"
        message += "Or file an issue here: https://github.com/sclorg/ci-scripts/issues"
        send_from = "phracek@redhat.com"
        send_to = ["phracek@redhat.com", "pkubat@redhat.com", "hhorak@redhat.com", "zmiklank@redhat.com"]
        msg = MIMEMultipart()
        msg['From'] = ', '.join(send_from)
        msg['To'] = ', '.join(send_to)
        msg['Subject'] = subject_msg
        msg.attach(MIMEText(message))
        if not self.global_result_flag:
            import glob
            log_files = glob.glob(f"{self.log_dir}/*.log")
            for log in log_files:
                attach = MIMEApplication(open(log, 'r').read(), Name=os.path.basename(str(log)))
                attach.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(str(log))))
                msg.attach(attach)
        smtp = smtplib.SMTP("127.0.0.1")
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()


if __name__ == "__main__":
    sanity_checker = SclOrgSanityChecker()
    if not sanity_checker.prepare():
        print("Preparation for GitHub Sanity checker has failed. Please look what's wrong.")
        sys.exit(1)
    sanity_checker.run_check()
    sanity_checker.send_email()
    sys.exit(0)
