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

default_mails = [
    "phracek@redhat.com",
    "hhorak@redhat.com",
    "pkubat@redhat.com",
    "anezbeda@redhat.com",
]
upstream_mails = [
    "phracek@redhat.com",
    "lholmqui@redhat.com",
    "nodeshiftcore@redhat.com",
]

SCLORG_MAILS = {
    # Format is 'repo_name', and list of mails to infor
    "s2i-ruby-container": ["jprokop@redhat.com"],
    "s2i-python-container": [
        "lbalhar@redhat.com",
        "ksurma@redhat.com",
        "thrnciar@redhat.com",
    ],
    "postgresql-container": ["fjanus@redhat.com", "ljavorsk@redhat.com"],
    "s2i-perl-container": ["jplesnik@redhat.com", "mspacek@redhat.com"],
    "s2i-nodejs-container": [
        "lholmqui@redhat.com",
        "cpapasta@redhat.com",
        "nodeshiftcore@redhat.com",
        "jprokop@redhat.com"
    ],
}

SCLORG_UPSTREAM_TESTS_MAILS = {
    "s2i-nodejs-container": [
        "lholmqui@redhat.com",
        "cpapasta@redhat.com",
        "nodeshiftcore@redhat.com",
    ]
}

TEST_CASES = {
    # Format is test for OS and king of test, what TMT Plan is used and MSG to mail
    ("fedora-test", "nightly-container-f", "Fedora test results:"),
    ("c9s-test", "nightly-container-centos-stream-9", "CentOS Stream 9 test results:"),
    (
        "c10s-test",
        "nightly-container-centos-stream-10",
        "CentOS Stream 10 test results:",
    ),
    ("rhel8-test", "nightly-container-rhel8", "RHEL-8 test results:"),
    (
        "rhel8-test-openshift-4",
        "nightly-container-rhel8",
        "RHEL-8 OpenShift 4 test results:",
    ),
    (
        "rhel8-test-openshift-pytest",
        "nightly-container-rhel8",
        "RHEL-8 PyTest in OpenShift 4 test results:",
    ),
    ("rhel9-test", "nightly-container-rhel9", "RHEL-9 test results:"),
    (
        "rhel9-test-openshift-4",
        "nightly-container-rhel9",
        "RHEL-9 OpenShift 4 test results:",
    ),
    (
        "rhel9-test-openshift-pytest",
        "nightly-container-rhel9",
        "RHEL-9 PyTest in OpenShift 4 test results:",
    ),
    (
        "rhel9-helm-charts",
        "nightly-container-rhel9",
        "RHEL-9 Helm Charts test results:",
    ),
    ("rhel10-test", "nightly-container-rhel10", "RHEL-10 test results:"),
}

TEST_UPSTREAM_CASES = {
    ("rhel8-test-upstream", "nightly-container-rhel8", "RHEL-8 Upstream test results:"),
    ("rhel9-test-upstream", "nightly-container-rhel9", "RHEL-9 Upstream test results:"),
    (
        "rhel10-test-upstream",
        "nightly-container-rhel10",
        "RHEL-10 Upstream test results:",
    ),
}

# The default directory used for nightly build
RESULTS_DIR = "/var/tmp/daily_reports_dir"


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
        self.full_success = False
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
            "--send-email",
            action="store_true",
            help="The logs are send over SMTP mail.",
            default=False,
        )
        parser.add_argument(
            "--upstream-tests",
            action="store_true",
            help="The logs are send over SMTP mail.",
            default=False,
        )
        parser.add_argument(
            "--log-dir", help="The logs are stored in user defined directory"
        )

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
        self.data_dict["tmt"] = {
            "logs": [],
            "msg": [],
            "tmt_running": [],
            "tmt_failed": [],
        }
        self.data_dict["SUCCESS"] = []
        self.data_dict["SUCCESS_DATA"] = []
        failed_tests = False
        for test_case, plan, _ in self.available_test_case:
            path_dir = Path(RESULTS_DIR) / test_case
            if not path_dir.is_dir():
                print(f"The test case {path_dir} does not exists that is weird")
                self.data_dict["tmt"]["msg"].append(
                    f"Nightly build tests for {test_case} is not finished or did not run. "
                    f"Check nightly build machine for logs."
                )
                failed_tests = True
                continue
            # It looks like TMT is still running for long time
            if (path_dir / "tmt_running").exists():
                self.data_dict["tmt"]["msg"].append(
                    f"tmt tests for case {test_case} is still running."
                    f"Look at log in attachment called '{test_case}-log.txt'."
                )
                self.data_dict["tmt"]["tmt_running"].append(test_case)
                self.data_dict["tmt"]["logs"].append(
                    (test_case, path_dir / "log.txt", "log.txt")
                )
                failed_tests = True
                continue
            # TMT command failed for some reason. Look at logs for given namespace
            # /var/tmp/daily_scl_tests/<test_case>/log.txt file
            if (path_dir / "tmt_failed").exists():
                self.data_dict["tmt"]["msg"].append(
                    f"tmt command has failed for test case {test_case}."
                    f"Look at log in attachment called '{test_case}-log.txt'."
                )
                self.data_dict["tmt"]["tmt_failed"].append(test_case)
                self.data_dict["tmt"]["logs"].append(
                    (test_case, path_dir / "log.txt", "log.txt")
                )
                failed_tests = True
                continue
            data_dir = path_dir / "plans" / plan / "data"
            if not data_dir.is_dir():
                self.data_dict["tmt"]["msg"].append(
                    f"Data dir for test case {test_case} does not exist."
                    f"Look at log in attachment called '{test_case}-log.txt'."
                )
                self.data_dict["tmt"]["logs"].append(
                    (test_case, path_dir / "log.txt", "log.txt")
                )
                failed_tests = True
                continue
            results_dir = data_dir / "results"
            failed_containers = list(results_dir.rglob("*.log"))
            if not failed_containers:
                self.data_dict["SUCCESS"].append(test_case)
                if self.args.upstream_tests:
                    success_logs = list(
                        (path_dir / "plans" / plan / "data").rglob("*.log")
                    )
                    self.data_dict["SUCCESS_DATA"].extend(
                        [(test_case, str(f), str(f.name)) for f in success_logs]
                    )
                continue
            print(f"Failed containers are for {test_case} are: {failed_containers}")
            failed_tests = True
            for cont in failed_containers:
                mime_name = f"{test_case}-{cont.name}"
                attach = MIMEApplication(open(cont, "r").read(), Name=mime_name)
                attach.add_header(
                    "Content-Disposition", 'attachment; filename="{}"'.format(mime_name)
                )
                self.mime_msg.attach(attach)
            self.data_dict[test_case] = [
                (str(f), str(f.name)) for f in failed_containers
            ]
        print(failed_tests)
        if not failed_tests:
            self.full_success = True
        print(f"collect data: {self.data_dict}")

    def generate_email_body(self):
        if self.args.upstream_tests:
            body_failure = "<b>NodeJS upstream tests failures:</b><br>"
            body_success = (
                "<b>NodeJS upstream tests were completely successful:</b><br>"
            )
        else:
            body_failure = "<b>Nightly builds Testing Farm failures:</b><br>"
            body_success = "<b>These nightly builds were completely successful:</b><br>"
        # Function for generation mail body
        if self.data_dict["tmt"]["msg"]:
            tmt_failures = "<br>".join(self.data_dict["tmt"]["msg"])
            self.body += (
                f"{body_failure}\n"
                f"Tests were not successful because Testing Farm failures. "
                f"Please contact phracek@redhat.com to analyse it.<br><br>"
                f"{tmt_failures}<br><br>"
            )
            self.generate_tmt_logs_containers()
        if self.data_dict["SUCCESS"]:
            success_tests = "<br>".join(self.data_dict["SUCCESS"])
            self.body += f"{body_success}{success_tests}<br><br>"
            if self.args.upstream_tests:
                self.generate_success_containers()

        self.generate_failed_containers()
        self.body += (
            "<br>In case the information is wrong, please reach out "
            "phracek@redhat.com, pkubat@redhat.com or hhorak@redhat.com.\n"
        )
        self.body += (
            "Or file an issue here: https://github.com/sclorg/ci-scripts/issues"
        )
        print(f"Body to email: {self.body}")

    def generate_failed_containers(self):
        for test_case, plan, msg in self.available_test_case:
            if test_case not in self.data_dict:
                continue
            print(f"generate_email_body: {self.data_dict[test_case]}")
            self.body += f"<br><b>{msg}</b><br>List of failed containers:<br>"
            for _, name in self.data_dict[test_case]:
                self.body += f"{name}<br>"

    def generate_success_containers(self):
        for test_case, cont_path, log_name in self.data_dict["SUCCESS_DATA"]:
            mime_name = f"{test_case}-{log_name}"
            if os.path.exists(cont_path):
                attach = MIMEApplication(open(cont_path, "r").read(), Name=mime_name)
                attach.add_header(
                    "Content-Disposition", 'attachment; filename="{}"'.format(mime_name)
                )
                self.mime_msg.attach(attach)

    def generate_tmt_logs_containers(self):
        for test_case, cont_path, log_name in self.data_dict["tmt"]["logs"]:
            mime_name = f"{test_case}-{log_name}"
            if os.path.exists(cont_path):
                attach = MIMEApplication(open(cont_path, "r").read(), Name=mime_name)
                attach.add_header(
                    "Content-Disposition", 'attachment; filename="{}"'.format(mime_name)
                )
                self.mime_msg.attach(attach)

    def generate_emails(self):
        for test_case, plan, _ in self.available_test_case:
            if test_case not in self.data_dict:
                continue
            for _, name in self.data_dict[test_case]:
                for cont, mails in SCLORG_MAILS.items():
                    if str(Path(name).with_suffix("")) != cont:
                        continue
                    self.add_email.extend(
                        [ml for ml in mails if ml not in self.add_email]
                    )

    def send_email(self):
        if not self.args.send_email:
            print("Sending email is not allowed")
            return
        if self.full_success:
            body_msg = "completely successful"
        else:
            body_msg = "some tests failed"
        if self.args.upstream_tests:
            subject_msg = f"Nightly Build report for NodeJS upstream tests - {body_msg}"
        else:
            subject_msg = (
                f"Nightly Build report test results over containers - {body_msg}"
            )

        send_from = "phracek@redhat.com"
        if self.args.upstream_tests:
            send_to = upstream_mails
        else:
            send_to = default_mails + self.add_email

        self.mime_msg["From"] = send_from
        self.mime_msg["To"] = ", ".join(send_to)
        self.mime_msg["Subject"] = subject_msg
        self.mime_msg.attach(MIMEText(self.body, "html"))
        smtp = smtplib.SMTP("127.0.0.1")
        smtp.sendmail(send_from, send_to, self.mime_msg.as_string())
        smtp.close()
        print("Sending email finished")


if __name__ == "__main__":
    ntr = NightlyTestsReport()
    if not ntr.prepare():
        print(
            "Preparation for NightlyBuild report has failed. Please look what's wrong."
        )
        sys.exit(1)
    ntr.collect_data()
    ntr.generate_email_body()
    ntr.generate_emails()
    ntr.send_email()
    sys.exit(0)
