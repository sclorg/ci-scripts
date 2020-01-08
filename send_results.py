#!/usr/bin/python
# -*- coding: utf-8 -*-
#
import smtplib
import sys

from pathlib import Path
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

COMMASPACE = ", "


class SendResults(object):

    results_dir: Path = None
    sender: str = ""
    recipients: List[str] = []
    msg: MIMEMultipart = None
    # Body message for an email
    html = """
        <html>
        <head></head>
            <body>
            <p>
                Nightly build testing of RHSCL containers {results}
                {cont}
            </p>
            </body>
        </html>
    """
    title: str = "RHSCL daily night build testing "

    def __init__(self):
        """
        Parse position arguments
        1st argument: directory
        2nd argument: sender
        3rd and rest arguments: recipients
        """
        self.get_cli_args()
        self.msg = MIMEMultipart()
        self.msg["From"] = self.sender
        self.msg["To"] = COMMASPACE.join(self.recipients)
        self.msg.preamble = self.title

    def get_cli_args(self):
        """
        Parse CLI arguments
        """
        # Directory, where are stored logs
        self.results_dir = Path(sys.argv[1])
        self.sender = sys.argv[2]
        self.recipients = sys.argv[3:]
        if not self.results_dir.exists() and not self.results_dir.is_dir():
            sys.exit(1)

    def iterate_over_dir(self) -> List:
        failed_containers: List = []
        for filename in self.results_dir.iterdir():
            print(filename)
            if not filename.is_file() and not str(filename).endswith(".log"):
                continue
            # Open log file and attach it into message
            with filename.open() as fp:
                file_attachment = MIMEText(fp.read(), "plain")
            file_attachment.add_header(
                "Content-Disposition", "attachment", filename=str(filename)
            )
            self.msg.attach(file_attachment)
            # Delete log file and append into failed_containers array
            failed_containers.append(filename)
            filename.unlink()
        return failed_containers

    def send_results(self):
        """
        Sends an email based on the logs from the given directory
        """
        failed_containers: List = self.iterate_over_dir()
        if failed_containers:
            short_result = "was successful."
            self.msg["Subject"] = self.title + short_result
            html = self.html.format(results=short_result, cont="")
        else:
            short_result = "failed."
            self.msg["Subject"] = self.title + short_result
            html = self.html.format(
                results=short_result,
                cont="<br>Failed containers: " + " ".join(failed_containers),
            )
        self.msg.attach(MIMEText(html, "html"))
        s = smtplib.SMTP("localhost")
        s.sendmail(self.sender, self.recipients, self.msg.as_string())
        s.quit()
        print("Results were sent")


if __name__ == "__main__":
    sr = SendResults()
    sr.send_results()
