#!/usr/bin/env python3
import os
import sys
import smtplib
import argparse

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List

default_mails = ["phracek@redhat.com", "hhorak@redhat.com", "pkubat@redhat.com", "zmiklank@redhat.com"]

SCLORG_MAILS = {
    # Format is 'repo_name', and list of mails to infor
    "s2i-perl-container": [""],
    "s2i-nodejs-container": [""],
    "s2i-php-container": [""],
    "s2i-ruby-container": ["jprokop@redhat.com"],
    "s2i-python-container": ["lbalhar@redhat.com"],
    "postgresql-container": ["fjanus@redhat.com"],
    "redis-container": [""],
    "varnish-container": [""],
    "mysql-container": [""],
    "mariadb-container": [""],
    "nginx-container": [""]
}


TEST_CASES = {
    ("fedora-test", "nightly-container-f", "Fedora test results:"),
    ("centos7-test", "nightly-container-centos-7", "CentOS 7 test results:"),
    ("centos7-openshift", "nightly-container-centos-7", "CentOS 7 OpenShift 3 test results:"),
    ("c9s-test", "nightly-container-centos-stream-9", "CentOS Stream 9 test results:"),
    ("c8s-test", "nightly-container-centos-stream-8", "CentOS Stream 8 test results:"),
    ("rhel7-test", "nightly-container-rhel7", "RHEL-7 test results:"),
    ("rhel7-test-openshift", "nightly-container-rhel7", "RHEL-7 OpenShift 3 test results:"),
    ("rhel7-test-openshift-4", "nightly-container-rhel7", "RHEL-7 OpenShift 4 test results:"),
    ("rhel8-test", "nightly-container-rhel8", "RHEL-8 test results:"),
    ("rhel8-test-openshift-4", "nightly-container-rhel8", "RHEL-8 OpenShift 4 test results:"),
    ("rhel9-test", "nightly-container-rhel9", "RHEL-9 test results:"),
    ("rhel9-test-openshift-4", "nightly-container-rhel9", "RHEL-9 OpenShift 4 test results:"),
}

# This is reference link to internal repository

RESULT_DIR = "/var/tmp/daily_scl_tests"


class NightlyTestsReport(object):
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
        self.failed_repos: List[str] = []
        self.log_dir = os.getcwd()
        self.mime_msg = MIMEMultipart()
        self.body = ""
        self.add_email = []

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="NightlyTestsReport program report all failures"
                        "over all OS and Tests (tests, test-openshift, test-openshift-4)."
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
        return True

    def collect_data(self):
        self.data_dict["tmt"] = []
        for test_case, plan, _ in TEST_CASES:
            path_dir = Path(RESULT_DIR) / test_case
            if not path_dir.is_dir():
                print(f"The test case {path_dir} does not exists that is weird")
                self.data_dict["tmt"].append(f"Nightly build tests for {test_case} is not finished or did not run. Check nightly build machine for logs.")
                continue
            if (path_dir / "tmt_running").exists():
                self.data_dict["tmt"].append(f"tmt tests for case {test_case} is still running."
                                             f"Look at it on nightly-build machine.")
                continue
            if (path_dir / "tmt_failed").exists():
                self.data_dict["tmt"].append(f"tmt command has failed for test case {test_case}."
                                             f"Look at it on nightly-build machine.")
                continue
            data_dir = path_dir / "plans" / plan / "data"
            print(f"Check if directory {data_dir} exists.")
            if not data_dir.is_dir():
                print(f"Data dir for test case {test_case} does not exist."
                      f"It looks like tmt command failed. See logs on nightly-build machine")
                continue
            results_dir = data_dir / "results"
            failed_containers = list(results_dir.rglob("*.log"))
            if not failed_containers:
                continue
            print(f"Failed containers are: {failed_containers}")
            for cont in failed_containers:
                mime_name = f"{test_case}-{cont.name}"
                if cont.name in SCLORG_MAILS:
                    self.add_email.extend(SCLORG_MAILS[cont.name])
                attach = MIMEApplication(open(cont, 'r').read(), Name=mime_name)
                attach.add_header('Content-Disposition', 'attachment; filename="{}"'.format(mime_name))
                self.mime_msg.attach(attach)
            self.data_dict[test_case] = [(str(f), str(f.name)) for f in failed_containers]
        print(self.data_dict)

    def generate_email_body(self):
        if self.data_dict["tmt"]:
            tmt_failures = '\n'.join(self.data_dict["tmt"])
            self.body += f"Nightly builds Testing Farm failures:\n{tmt_failures}\n\n"
        for test_case, plan, msg in TEST_CASES:
            if test_case not in self.data_dict:
                continue
            print(self.data_dict[test_case])
            self.body += f"\n{msg}\nList of failed containers:\n"
            for _, name in self.data_dict[test_case]:
                self.body += f"{name}\n"
        self.body += "\nIn case the information is wrong, please reach out " \
                   "phracek@redhat.com, pkubat@redhat.com or hhorak@redhat.com.\n"
        self.body += "Or file an issue here: https://github.com/sclorg/ci-scripts/issues"
        print(self.body)

    def generate_email_recepients(self):
        pass

    def send_email(self):
        if not self.args.send_email:
            print("Sending email is not allowed")
            return
        subject_msg = "Nightly Build report test results over containers"

        send_from = "phracek@redhat.com"
        send_to = default_mails + self.add_email
        print(send_to)
        send_to = "phracek@redhat.com"

        self.mime_msg['From'] = send_from#', '.join(send_from)
        self.mime_msg['To'] = send_to #', '.join(send_to)
        self.mime_msg['Subject'] = subject_msg
        self.mime_msg.attach(MIMEText(self.body))
        smtp = smtplib.SMTP("127.0.0.1")
        smtp.sendmail(send_from, send_to, self.mime_msg.as_string())
        smtp.close()


if __name__ == "__main__":
    ntr = NightlyTestsReport()
    if not ntr.prepare():
        print("Preparation for NightlyBuild report has failed. Please look what's wrong.")
        sys.exit(1)
    ntr.collect_data()
    ntr.generate_email_body()
    ntr.send_email()
    sys.exit(0)
