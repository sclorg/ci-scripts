#!/usr/bin/env python3
import os
import sys
import smtplib
import argparse
import subprocess
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List

default_mails = [
    "phracek@redhat.com",
    "hhorak@redhat.com",
    "pkubat@redhat.com",
    "anezbeda@redhat.com",
    "pkhartsk@redhat.com",
]
upstream_mails = [
    "phracek@redhat.com",
    "cpapasta@redhat.com",
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
    "postgresql-container": [
        "fjanus@redhat.com",
        "ljavorsk@redhat.com",
        "mschorm@redhat.com",
        "psloboda@redhat.com",
    ],
    "mariadb-container": [
        "fjanus@redhat.com",
        "ljavorsk@redhat.com",
        "mschorm@redhat.com",
        "psloboda@redhat.com",
    ],
    "mysql-container": [
        "fjanus@redhat.com",
        "ljavorsk@redhat.com",
        "mschorm@redhat.com",
        "psloboda@redhat.com",
    ],
    "s2i-perl-container": ["jplesnik@redhat.com", "mspacek@redhat.com"],
    "s2i-nodejs-container": [
        "cpapasta@redhat.com",
        "nodeshiftcore@redhat.com",
        "jprokop@redhat.com",
    ],
}

SCLORG_UPSTREAM_TESTS_MAILS = {
    "s2i-nodejs-container": ["cpapasta@redhat.com", "nodeshiftcore@redhat.com"]
}

TEST_CASES = {
    # Format is test for OS and king of test, what TMT Plan is used and MSG to mail
    ("fedora-test", "nightly-container-fedora", "Fedora test results:"),
    ("fedora-test-pytest", "nightly-container-fedora", "Fedora PyTest test results:"),
    ("c9s-test", "nightly-container-c9s", "CentOS Stream 9 test results:"),
    (
        "c9s-test-pytest",
        "nightly-container-c9s",
        "CentOS Stream 9 PyTest test results:",
    ),
    ("c10s-test", "nightly-container-c10s", "CentOS Stream 10 test results:"),
    (
        "c10s-test-pytest",
        "nightly-container-c10s",
        "CentOS Stream 10 PyTest test results:",
    ),
    ("rhel8-test", "nightly-container-rhel8", "RHEL-8 test results:"),
    ("rhel8-test-pytest", "nightly-container-rhel8", "RHEL-8 PyTest test results:"),
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
    ("rhel9-test-pytest", "nightly-container-rhel8", "RHEL-9 PyTest test results:"),
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
    ("rhel10-test-pytest", "nightly-container-rhel10", "RHEL-10 PyTest test results:"),
    (
        "rhel10-test-openshift-4",
        "nightly-container-rhel10",
        "RHEL-10 OpenShift 4 test results:",
    ),
    (
        "rhel10-test-openshift-pytest",
        "nightly-container-rhel10",
        "RHEL-10 PyTest in OpenShift 4 test results:",
    ),
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
# The default directory used for running build
SCLORG_DIR = "/var/tmp/daily_scl_tests"


def run_command(
    cmd,
    return_output: bool = True,
    ignore_error: bool = False,
    shell: bool = True,
    **kwargs,
):
    """
    Run provided command on host system using the same user as invoked this code.
    Raises subprocess.CalledProcessError if it fails.
    :param cmd: list or str
    :param return_output: bool, return output of the command
    :param ignore_error: bool, do not fail in case nonzero return code
    :param shell: bool, run command in shell
    :param debug: bool, print command in shell, default is suppressed
    :return: None or str
    """
    print(f"command: {cmd}")
    try:
        if return_output:
            return subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=shell,
                **kwargs,
            )
        else:
            return subprocess.check_call(cmd, shell=shell, **kwargs)
    except subprocess.CalledProcessError as cpe:
        if ignore_error:
            if return_output:
                return cpe.output
            else:
                return cpe.returncode
        else:
            print(f"failed with code {cpe.returncode} and output:\n{cpe.output}")
            raise cpe


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

    def send_file_to_pastebin(self, log_path, log_name: str):
        if not os.path.exists(log_path):
            return
        send_paste_bin = os.getenv("HOME") + "/ci-scripts/send_to_paste_bin.sh"
        cmd = f'{send_paste_bin} "{log_path}" "{log_name}"'
        print(f"sending logs to pastebin: {cmd}")
        for count in range(5):
            try:
                run_command(cmd)
                break
            except subprocess.CalledProcessError:
                print(f"ERROR: Sending to pastebin by command {cmd} failed")
                pass
            time.sleep(3)

    def get_pastebin_url(self, log_name: str) -> str:
        with open(log_name, "r") as f:
            lines = f.read()

        for line in lines.split("\n"):
            if not line.startswith("Link:"):
                continue
            return line.replace("Link:", "").strip()
        return ""

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
                continue
            # It looks like TMT is still running for long time
            if (path_dir / "tmt_running").exists():
                self.data_dict["tmt"]["msg"].append(
                    f"tmt tests for case {test_case} is still running."
                    f"Look at log in attachment called '{test_case}-log.txt'."
                )
                self.data_dict["tmt"]["tmt_running"].append(test_case)
                for sclorg in ["S2I", "NOS2I"]:
                    name = f"{test_case}-{sclorg}"
                    self.send_file_to_pastebin(
                        log_path=Path(SCLORG_DIR) / f"{name}" / "log.txt",
                        log_name=f"{path_dir}/{name}.log.txt",
                    )
                    self.data_dict["tmt"]["logs"].append(
                        (
                            name,
                            Path(SCLORG_DIR) / f"{name}" / "log.txt",
                            Path(path_dir) / f"{name}.log.txt",
                        )
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
                for sclorg in ["S2I", "NOS2I"]:
                    name = f"{test_case}-{sclorg}"
                    self.send_file_to_pastebin(
                        log_path=Path(SCLORG_DIR) / f"{name}" / "log.txt",
                        log_name=f"{path_dir}/{name}.log.txt",
                    )
                    self.data_dict["tmt"]["logs"].append(
                        (
                            name,
                            Path(SCLORG_DIR) / f"{name}" / "log.txt",
                            Path(path_dir) / f"{name}.log.txt",
                        )
                    )
                failed_tests = True
                continue
            data_dir = path_dir / "plans" / plan / "data"
            if not data_dir.is_dir():
                self.data_dict["tmt"]["msg"].append(
                    f"Data dir for test case {test_case} does not exist."
                    f"Look at log in attachment called '{test_case}-log.txt'."
                )
                for sclorg in ["S2I", "NOS2I"]:
                    name = f"{test_case}-{sclorg}"
                    self.send_file_to_pastebin(
                        log_path=Path(SCLORG_DIR) / f"{name}" / "log.txt",
                        log_name=f"{path_dir}/{name}.log.txt",
                    )
                    self.data_dict["tmt"]["logs"].append(
                        (
                            name,
                            Path(SCLORG_DIR) / f"{name}" / "log.txt",
                            Path(path_dir) / f"{name}.log.txt",
                        )
                    )
                failed_tests = True
                continue
            results_dir = data_dir / "results"
            print("Results dir is for failed_container: ", results_dir)
            failed_containers = list(results_dir.rglob("*.log"))
            print("Failed containers are: ", failed_containers)
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

            self.data_dict[test_case] = [
                (str(f), str(f.name)) for f in failed_containers
            ]
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
            self.body += (
                f"{body_failure}\n"
                f"Tests were not successful because Testing Farm failures. "
                f"Please contact phracek@redhat.com to analyse it.<br><br>"
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
            print(
                f"generate_email_body_for_failed_containers: {self.data_dict[test_case]}"
            )
            self.body += f"<br><b>{msg}</b><br>List of failed containers:<br>"
            for full_log_name, name in self.data_dict[test_case]:
                paste_bin_file = f"{full_log_name}.txt"
                self.send_file_to_pastebin(
                    log_path=full_log_name, log_name=paste_bin_file
                )
                self.body += (
                    f"<a href='{self.get_pastebin_url(log_name=paste_bin_file)}'>{name}</a>"
                    f"<br>"
                )

    def generate_success_containers(self):
        for test_case, cont_path, log_name in self.data_dict["SUCCESS_DATA"]:
            print(f"generate_success_containers: {self.data_dict[test_case]}")
            if os.path.exists(log_name):
                self.body += (
                    f" <a href='{self.get_pastebin_url(log_name=log_name)}'>See logs</a>"
                    f"<br>"
                )

    def generate_tmt_logs_containers(self):
        for test_case, cont_path, log_name in self.data_dict["tmt"]["logs"]:
            print(test_case, cont_path, log_name)
            if os.path.exists(log_name):
                self.body += (
                    f"<b>{test_case}</b> <a href='{self.get_pastebin_url(log_name=log_name)}'>"
                    f"See logs</a>"
                    f"<br>"
                )
            else:
                self.body += (
                    f"<b>{test_case}</b> No logs available. "
                    f"Check nightly build machine<br>"
                )
        self.body += "<br>"

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
