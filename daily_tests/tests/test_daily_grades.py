# pylint: disable=import-error,redefined-outer-name
import importlib
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture
def daily_grades_module():
    fake_main = types.ModuleType("rh_cwt.main")

    class FakeRhelImageRebuilder:
        def __init__(self, base_image):
            self.base_image = base_image
            self.exclude_image = None
            self.configs = []
            self.last_config = None
            self.grades_by_config = {}

        def set_config(self, config):
            self.last_config = config
            self.configs.append(config)

        def check_rhcc_grades(self):
            return self.grades_by_config.get(self.last_config, [])

    fake_main.RhelImageRebuilder = FakeRhelImageRebuilder
    fake_pkg = types.ModuleType("rh_cwt")
    fake_pkg.main = fake_main

    original_modules = {
        "rh_cwt": sys.modules.get("rh_cwt"),
        "rh_cwt.main": sys.modules.get("rh_cwt.main"),
        "daily_grades": sys.modules.get("daily_grades"),
    }
    sys.modules["rh_cwt"] = fake_pkg
    sys.modules["rh_cwt.main"] = fake_main

    daily_tests_dir = Path(__file__).resolve().parents[1] / "daily_tests"
    original_sys_path = list(sys.path)
    sys.path.insert(0, str(daily_tests_dir))

    try:
        module = importlib.import_module("daily_grades")
        importlib.reload(module)
        yield module
    finally:
        sys.path[:] = original_sys_path
        if original_modules["daily_grades"] is None:
            sys.modules.pop("daily_grades", None)
        else:
            sys.modules["daily_grades"] = original_modules["daily_grades"]
        if original_modules["rh_cwt"] is None:
            sys.modules.pop("rh_cwt", None)
        else:
            sys.modules["rh_cwt"] = original_modules["rh_cwt"]
        if original_modules["rh_cwt.main"] is None:
            sys.modules.pop("rh_cwt.main", None)
        else:
            sys.modules["rh_cwt.main"] = original_modules["rh_cwt.main"]


@pytest.fixture
def report(daily_grades_module):
    return daily_grades_module.DailyGradesReport()


@pytest.fixture
def smtp_spy(daily_grades_module):
    instances = []
    original_smtp = daily_grades_module.smtplib.SMTP

    class FakeSMTP:
        def __init__(self, host):
            self.host = host
            self.sent = []
            self.closed = False
            instances.append(self)

        def sendmail(self, send_from, send_to, msg):
            self.sent.append((send_from, send_to, msg))

        def close(self):
            self.closed = True

    daily_grades_module.smtplib.SMTP = FakeSMTP
    try:
        yield instances
    finally:
        daily_grades_module.smtplib.SMTP = original_smtp


def test_get_grades_collects_all_configs(report):
    report.rhcwt_api.grades_by_config = {
        "rhel8.yaml": [("nodejs", "A", 0)],
        "rhel9.yaml": [("php", "B", 2)],
        "rhel10.yaml": [("python", "C", 1)],
    }

    report.get_grades()

    assert report.grades_dict["RHEL8"] == [("nodejs", "A", 0)]
    assert report.grades_dict["RHEL9"] == [("php", "B", 2)]
    assert report.grades_dict["RHEL10"] == [("python", "C", 1)]
    assert report.rhcwt_api.exclude_image == "nodejs-10"
    assert report.rhcwt_api.configs == ["rhel8.yaml", "rhel9.yaml", "rhel10.yaml"]


def test_check_grades_builds_body(report):
    report.grades_dict = {
        "RHEL8": [("nodejs", "B", 5), ("ruby", "NONE", 0)],
        "RHEL9": [("php", "C", 3)],
        "RHEL10": [("python", "D", -2)],
    }

    report.check_grades()

    assert "Nightly report for container grades for RHEL8" in report.body
    assert "nodejs [B] 5 days until grade C!" in report.body
    assert "Some images were not found in container catalog." in report.body
    assert "php [C] 3 days since grade C!" in report.body
    assert "python [D] 2 days last grade change!" in report.body
    assert "The rest of images are in grade A." in report.body


def test_send_email_uses_smtp(report, smtp_spy):
    report.body = "<b>Report</b>"

    report.send_email()

    assert smtp_spy
    instance = smtp_spy[0]
    assert instance.host == "127.0.0.1"
    assert instance.closed is True
    assert instance.sent
    send_from, send_to, msg = instance.sent[0]
    assert send_from == "phracek@redhat.com"
    assert "Container Grades" in msg
    assert ", ".join(send_to) in msg
