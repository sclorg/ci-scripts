#!/usr/bin/env python3
import os
import sys
import smtplib
import subprocess

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict

from rh_cwt.main import RhelImageRebuilder

default_mails = [
    "phracek@redhat.com",
    "hhorak@redhat.com",
    "pkubat@redhat.com",
    "anezbeda@redhat.com",
]

GRADES_OS_DICT = {"RHEL8": "rhel8.yaml", "RHEL9": "rhel9.yaml", "RHEL10": "rhel10.yaml"}


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


class DailyGradesReport(object):
    def __init__(self):
        self.tmp_path_dir: Path
        self.cwd = os.getcwd()
        self.report_file: str = ""
        self.report_text_filename: str = ""
        self.log_dir = os.getcwd()
        self.mime_msg = MIMEMultipart()
        self.body = ""
        self.add_email = []
        self.grades_dict = {}
        self.body = ""
        self.rhcwt_api = RhelImageRebuilder(base_image="WHATEVER")

    def get_grades(self):
        for OS in GRADES_OS_DICT.keys():
            self.grades_dict[OS] = self.get_grades_for_OS(GRADES_OS_DICT[OS])
        print(f"GRADES_DICT = {self.grades_dict}.")

    def get_grades_for_OS(self, config) -> Dict:
        if config == "rhel8.yaml":
            self.rhcwt_api.exclude_image = "nodejs-10"
        self.rhcwt_api.set_config(config)
        return self.rhcwt_api.check_rhcc_grades()

    def check_grades(self):
        for OS in self.grades_dict.keys():
            self.body += f"<b>Nightly report for container grades for {OS} is:</b><br>"
            grade_none = False
            grade_flags = True
            for image_grade_info in self.grades_dict[OS]:
                image_name, current_grade, days = image_grade_info
                if current_grade == "B":
                    self.body += (
                        f"{image_name} [{current_grade}] days until grade C!<br>"
                    )
                    grade_flags = False
                if current_grade == "C":
                    self.body += (
                        f"{image_name} [{current_grade}] days since grade C!<br>"
                    )
                    grade_flags = False
                if current_grade == "NONE":
                    grade_none = True
            if grade_flags:
                self.body += f"All images for {OS} are in grade A. <br><br>"
            if grade_none:
                self.body += (
                    "Some images were not found in container catalog."
                    "Please take a look at it.<br>"
                )
            if not grade_flags:
                self.body += "The rest of images are in grade A. <br><br>"
        self.body += (
            "In case the information is wrong,"
            "please reach out to phracek@redhat.com, pkubat@redhat.com, or hhorak@redhat.com.<br>"
        )
        self.body += (
            "Or file an issue here: https://github.com/sclorg/ci-scripts/issues<br>"
        )

    def send_email(self):
        send_from = "phracek@redhat.com"
        self.mime_msg["From"] = send_from
        self.mime_msg["To"] = ", ".join(default_mails)
        self.mime_msg[
            "Subject"
        ] = "[CS Image Grading] Container Grades of Apps&Stack images for RHEL8, RHEL9 and RHEL10"
        self.mime_msg.attach(MIMEText(self.body, "html"))
        smtp = smtplib.SMTP("127.0.0.1")
        smtp.sendmail(send_from, default_mails, self.mime_msg.as_string())
        smtp.close()
        print("Sending email finished")


if __name__ == "__main__":
    dgr = DailyGradesReport()
    dgr.get_grades()
    dgr.check_grades()
    dgr.send_email()
    sys.exit(0)
