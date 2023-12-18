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
upstream_mails = ["lholmqui@redhat.com", "nodeshiftcore@redhat.com"]

SCLORG_MAILS = {
    # Format is 'repo_name', and list of mails to infor
    "s2i-ruby-container": ["jprokop@redhat.com"],
    "s2i-python-container": ["lbalhar@redhat.com"],
    "postgresql-container": ["fjanus@redhat.com"],
    "s2i-perl-container": ["jplesnik@redhat.com", "mspacek@redhat.com"],
}

SCLORG_UPSTREAM_TESTS_MAILS = {
    "s2i-nodejs-container": ["lholmqui@redhat.com", "nodeshiftcore@redhat.com"],
}

TEST_CASES = {
    # Format is test for OS and king of test, what TMT Plan is used and MSG to mail
    ("fedora-test", "nightly-container-f", "Fedora test results:"),
    ("c9s-test", "nightly-container-centos-stream-9", "CentOS Stream 9 test results:"),
    ("c8s-test", "nightly-container-centos-stream-8", "CentOS Stream 8 test results:"),
    ("rhel7-test", "nightly-container-rhel7", "RHEL-7 test results:"),
    # Starting OpenShift 3 causing problems on RHEL-7. Suppressing it.
    # ("rhel7-test-openshift", "nightly-container-rhel7", "RHEL-7 OpenShift 3 test results:"),
    ("rhel7-test-openshift-4", "nightly-container-rhel7", "RHEL-7 OpenShift 4 test results:"),
    ("rhel8-test", "nightly-container-rhel8", "RHEL-8 test results:"),
    ("rhel8-test-openshift-4", "nightly-container-rhel8", "RHEL-8 OpenShift 4 test results:"),
    ("rhel9-test", "nightly-container-rhel9", "RHEL-9 test results:"),
    ("rhel9-test-openshift-4", "nightly-container-rhel9", "RHEL-9 OpenShift 4 test results:"),
}

TEST_UPSTREAM_CASES = {
    ("rhel7-test-upstream", "nightly-container-rhel7", "RHEL-7 Upstream test results:"),
    ("rhel8-test-upstream", "nightly-container-rhel8", "RHEL-8 Upstream test results:"),
    ("rhel9-test-upstream", "nightly-container-rhel9", "RHEL-9 Upstream test results:"),
}

# The default directory used for nightly build
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
        if self.args.upstream_tests:
            self.available_test_case = TEST_UPSTREAM_CASES
        else:
            self.available_test_case = TEST_CASES

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="NightlyTestsReport program report all failures"
                        "over all OS and Tests (tests, test-openshift, test-openshift-4)."
        )
        parser.add_argument(
            "--send-email", action="store_true", help="The logs are send over SMTP mail.", default=False
        )
        parser.add_argument(
            "--upstream-tests", action="store_true", help="The logs are send over SMTP mail.", default=False
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
        # Collect data to class dictionary
        # self.data_dict['tmt'] item is used for Testing Farm errors per each OS and test case
        # self.data_dict[test_case] contains failed logs for given test case. E.g. 'fedora-test'
        self.data_dict["tmt"] = []
        self.data_dict["SUCCESS"] = []
        for test_case, plan, _ in self.available_test_case:
            path_dir = Path(RESULT_DIR) / test_case
            if not path_dir.is_dir():
                print(f"The test case {path_dir} does not exists that is weird")
                self.data_dict["tmt"].append(f"Nightly build tests for {test_case} is not finished or did not run. Check nightly build machine for logs.")
                continue
            # It looks like TMT is still running for long time
            if (path_dir / "tmt_running").exists():
                self.data_dict["tmt"].append(f"tmt tests for case {test_case} is still running."
                                             f"Look at it on nightly-build machine.")
                continue
            # TMT command failed for some reason. Look at logs for given namespace
            # /var/tmp/daily_scl_tests/<test_case>/log.txt file
            if (path_dir / "tmt_failed").exists():
                self.data_dict["tmt"].append(f"tmt command has failed for test case {test_case}."
                                             f"Look at it on nightly-build machine.")
                continue
            data_dir = path_dir / "plans" / plan / "data"
            if not data_dir.is_dir():
                print(f"Data dir for test case {test_case} does not exist."
                      f"It looks like tmt command failed. See logs on nightly-build machine")
                continue
            results_dir = data_dir / "results"
            failed_containers = list(results_dir.rglob("*.log"))
            if not failed_containers:
                self.data_dict["SUCCESS"].append(test_case)
                continue
            print(f"Failed containers are for {test_case} are: {failed_containers}")
            for cont in failed_containers:
                mime_name = f"{test_case}-{cont.name}"
                attach = MIMEApplication(open(cont, 'r').read(), Name=mime_name)
                attach.add_header('Content-Disposition', 'attachment; filename="{}"'.format(mime_name))
                self.mime_msg.attach(attach)
            self.data_dict[test_case] = [(str(f), str(f.name)) for f in failed_containers]
        print(f"collect data: {self.data_dict}")

    def generate_email_body(self):
        if self.args.upstream_tests:
            body_failure = "NodeJS upstream tests failures:"
            body_success = "NodeJS upstream tests were completely successful:"
        else:
            body_failure = "Nightly builds Testing Farm failures:"
            body_success = "These nightly builds were completely successful:"
        # Function for generation mail body
        if self.data_dict["tmt"]:
            tmt_failures = '\n'.join(self.data_dict["tmt"])
            self.body += f"{body_failure}\n{tmt_failures}\n\n"
        if self.data_dict["SUCCESS"]:
            success_tests = '\n'.join(self.data_dict["SUCCESS"])
            self.body += f"{body_success}\n{success_tests}\n\n"
        for test_case, plan, msg in self.available_test_case:
            if test_case not in self.data_dict:
                continue
            print(f"generate_email_body: {self.data_dict[test_case]}")
            self.body += f"\n{msg}\nList of failed containers:\n"
            for _, name in self.data_dict[test_case]:
                self.body += f"{name}\n"
        self.body += "\nIn case the information is wrong, please reach out " \
                   "phracek@redhat.com, pkubat@redhat.com, zmiklank@redhat.com or hhorak@redhat.com.\n"
        self.body += "Or file an issue here: https://github.com/sclorg/ci-scripts/issues"
        print(f"Body to email: {self.body}")

    def generate_emails(self):
        for test_case, plan, _ in self.available_test_case:
            if test_case not in self.data_dict:
                continue
            for _, name in self.data_dict[test_case]:
                for cont, mails in SCLORG_MAILS.items():
                    if str(Path(name).with_suffix('')) != cont:
                        continue
                    self.add_email.extend([ml for ml in mails if ml not in self.add_email])

    def send_email(self):
        if not self.args.send_email:
            print("Sending email is not allowed")
            return
        if self.args.upstream_tests:
            subject_msg = "Nightly Build report for NodeJS upstream tests"
        else:
            subject_msg = "Nightly Build report test results over containers"

        send_from = "phracek@redhat.com"
        if self.args.upstream_tests:
            send_to = upstream_mails
        else:
            send_to = default_mails + self.add_email

        self.mime_msg['From'] = send_from
        self.mime_msg['To'] = ', '.join(send_to)
        self.mime_msg['Subject'] = subject_msg
        self.mime_msg.attach(MIMEText(self.body))
        smtp = smtplib.SMTP("127.0.0.1")
        smtp.sendmail(send_from, send_to, self.mime_msg.as_string())
        smtp.close()
        print("Sending email finished")


if __name__ == "__main__":
    ntr = NightlyTestsReport()
    if not ntr.prepare():
        print("Preparation for NightlyBuild report has failed. Please look what's wrong.")
        sys.exit(1)
    ntr.collect_data()
    ntr.generate_email_body()
    ntr.generate_emails()
    ntr.send_email()
    sys.exit(0)
