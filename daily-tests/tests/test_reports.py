# pylint: disable=import-error,redefined-outer-name,protected-access
"""Tests for daily_nightly_tests_report."""

import sys
from pathlib import Path

import pytest
from flexmock import flexmock

from daily_tests import daily_nightly_tests_report as nightly_mod
from daily_tests.daily_nightly_tests_report import NightlyTestsReport

TEST_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(TEST_DIR.parent))


@pytest.fixture
def nightly_report(monkeypatch):
    """Build NightlyTestsReport with argv that avoids argparse errors."""
    monkeypatch.setattr(sys, "argv", ["daily_nightly_tests_report.py"])
    return NightlyTestsReport()


@pytest.fixture
def reset_sclorg_mails():
    """Isolate module-level SCLORG_MAILS across tests."""
    backup = dict(nightly_mod.SCLORG_MAILS)
    nightly_mod.SCLORG_MAILS.clear()
    yield
    nightly_mod.SCLORG_MAILS.clear()
    nightly_mod.SCLORG_MAILS.update(backup)


@pytest.fixture
def collect_report(nightly_report, monkeypatch, tmp_path):
    """NightlyTestsReport with a single test case and tmp reports_dir."""
    nightly_report.reports_dir = tmp_path
    monkeypatch.setattr(
        nightly_report,
        "available_test_case",
        {("fedora-test", "nightly-fedora", "Fedora test results:")},
    )
    flexmock(nightly_report).should_receive("send_file_to_pastebin")
    return nightly_report


class TestDailyNightlyTestsReport:
    """Tests for NightlyTestsReport."""

    def test_get_env_variable_missing_returns_default_empty(
        self, nightly_report, monkeypatch
    ):
        monkeypatch.delenv("TEST_VAR_GET_ENV", raising=False)
        assert nightly_report._get_env_variable("TEST_VAR_GET_ENV") == ""

    def test_get_env_variable_missing_returns_explicit_default(
        self, nightly_report, monkeypatch
    ):
        monkeypatch.delenv("TEST_VAR_GET_ENV", raising=False)
        got = nightly_report._get_env_variable("TEST_VAR_GET_ENV", "fallback")
        assert got == "fallback"

    def test_get_env_variable_set_returns_value(self, nightly_report, monkeypatch):
        monkeypatch.setenv("TEST_VAR_GET_ENV", "from-env")
        assert nightly_report._get_env_variable("TEST_VAR_GET_ENV") == "from-env"

    def test_get_env_variable_set_empty_string_returns_empty(
        self, nightly_report, monkeypatch
    ):
        monkeypatch.setenv("TEST_VAR_GET_ENV", "")
        assert nightly_report._get_env_variable("TEST_VAR_GET_ENV", "ignored") == ""


def _env_for_load_mails(**overrides):
    """Minimal env so load_mails_from_environment completes without error."""
    base = {
        "DB_MAILS": "db1@example.com,db2@example.com",
        "RUBY_MAILS": "ruby@example.com",
        "PYTHON_MAILS": "py@example.com",
        "NODEJS_MAILS": "node@example.com",
        "PERL_MAILS": "perl@example.com",
        "UPSTREAM_MAILS": "up@example.com",
        "DEFAULT_MAILS": "def1@example.com,def2@example.com",
        "NIGHTLY_BUILDS_URL": "https://nightly.example",
        "SEND_EMAIL": "",
    }
    base.update(overrides)
    return base


class TestLoadMailsFromEnvironment:
    """Tests for NightlyTestsReport.load_mails_from_environment."""

    def test_load_mails_from_environment_populates_sclorg_and_report_fields(
        self, nightly_report, reset_sclorg_mails, monkeypatch
    ):
        env = _env_for_load_mails(
            SMTP_SERVER="smtp.custom.example.com", SMTP_PORT="465"
        )
        for key, val in env.items():
            monkeypatch.setenv(key, val, prepend=False)

        nightly_report.load_mails_from_environment()

        db_list = ["db1@example.com", "db2@example.com"]
        assert nightly_mod.SCLORG_MAILS["mariadb-container"] == db_list
        assert nightly_mod.SCLORG_MAILS["mysql-container"] == db_list
        assert nightly_mod.SCLORG_MAILS["postgresql-container"] == db_list
        assert nightly_mod.SCLORG_MAILS["s2i-ruby-container"] == ["ruby@example.com"]
        assert nightly_mod.SCLORG_MAILS["s2i-python-container"] == ["py@example.com"]
        assert nightly_mod.SCLORG_MAILS["s2i-nodejs-container"] == ["node@example.com"]
        assert nightly_mod.SCLORG_MAILS["s2i-perl-container"] == ["perl@example.com"]
        assert nightly_mod.SCLORG_MAILS["upstream-tests"] == ["up@example.com"]
        assert nightly_report.smtp_server == "smtp.custom.example.com"
        assert nightly_report.smtp_port == 465
        assert nightly_report.default_mails == ["def1@example.com", "def2@example.com"]
        assert nightly_report.nightly_builds_url == "https://nightly.example"
        assert nightly_report.send_email is False

    def test_load_mails_from_environment_smtp_defaults_when_unset(
        self, nightly_report, reset_sclorg_mails, monkeypatch
    ):
        for key, val in _env_for_load_mails().items():
            monkeypatch.setenv(key, val, prepend=False)
        monkeypatch.delenv("SMTP_SERVER", raising=False)
        monkeypatch.delenv("SMTP_PORT", raising=False)

        nightly_report.load_mails_from_environment()

        assert nightly_report.smtp_server == "smtp.redhat.com"
        assert nightly_report.smtp_port == 25


class TestGetPastebinUrl:
    """Tests for NightlyTestsReport.get_pastebin_url."""

    def test_get_pastebin_url_returns_url_from_link_line(
        self, nightly_report, tmp_path
    ):
        link_file = tmp_path / "paste.txt"
        link_file.write_text(
            "some noise\nLink:   https://paste.example.com/abc   \ntail\n",
            encoding="utf-8",
        )
        assert (
            nightly_report.get_pastebin_url(str(link_file))
            == "https://paste.example.com/abc"
        )

    def test_get_pastebin_url_returns_first_link_line(self, nightly_report, tmp_path):
        link_file = tmp_path / "paste.txt"
        link_file.write_text(
            "Link: https://first.example\nLink: https://second.example\n",
            encoding="utf-8",
        )
        assert nightly_report.get_pastebin_url(str(link_file)) == (
            "https://first.example"
        )

    def test_get_pastebin_url_returns_empty_when_no_link_line(
        self, nightly_report, tmp_path
    ):
        link_file = tmp_path / "paste.txt"
        link_file.write_text("no url here\nhttps://ignored\n", encoding="utf-8")
        assert nightly_report.get_pastebin_url(str(link_file)) == ""

    def test_get_pastebin_url_returns_empty_for_empty_file(
        self, nightly_report, tmp_path
    ):
        link_file = tmp_path / "paste.txt"
        link_file.write_text("", encoding="utf-8")
        assert nightly_report.get_pastebin_url(str(link_file)) == ""


class TestCollectData:
    """Tests for NightlyTestsReport.collect_data."""

    def test_collect_data_full_success_when_no_failed_logs(self, collect_report):
        case_dir = collect_report.reports_dir / "fedora-test"
        (case_dir / "results").mkdir(parents=True)

        collect_report.collect_data()

        assert collect_report.full_success is True
        assert collect_report.data_dict["SUCCESS"] == ["fedora-test"]
        assert collect_report.data_dict["tmt"]["tmt_running"] == []
        assert collect_report.data_dict["tmt"]["tmt_failed"] == []

    def test_collect_data_records_failed_container_logs(self, collect_report):
        case_dir = collect_report.reports_dir / "fedora-test"
        log_file = case_dir / "results" / "ns" / "failed.log"
        log_file.parent.mkdir(parents=True)
        log_file.write_text("err", encoding="utf-8")

        collect_report.collect_data()

        assert collect_report.full_success is False
        assert "fedora-test" in collect_report.data_dict
        assert collect_report.data_dict["fedora-test"] == [
            (str(log_file), "failed.log")
        ]

    def test_collect_data_skips_when_reports_dir_missing(
        self, nightly_report, monkeypatch, tmp_path
    ):
        nightly_report.reports_dir = tmp_path / "does_not_exist"
        monkeypatch.setattr(
            nightly_report,
            "available_test_case",
            {("fedora-test", "nightly-fedora", "Fedora test results:")},
        )

        nightly_report.collect_data()

        assert nightly_report.full_success is True
        assert nightly_report.data_dict["SUCCESS"] == []

    def test_collect_data_skips_when_test_case_dir_missing(self, collect_report):
        collect_report.collect_data()

        assert collect_report.full_success is True
        assert collect_report.data_dict["SUCCESS"] == []

    def test_collect_data_tmt_running(self, collect_report):
        case_dir = collect_report.reports_dir / "fedora-test"
        case_dir.mkdir(parents=True)
        (case_dir / "tmt_running").write_text("", encoding="utf-8")

        collect_report.collect_data()

        assert collect_report.full_success is False
        assert collect_report.data_dict["tmt"]["tmt_running"] == ["fedora-test"]
        assert "fedora-test" not in collect_report.data_dict["SUCCESS"]

    def test_collect_data_tmt_failed(self, collect_report):
        case_dir = collect_report.reports_dir / "fedora-test"
        case_dir.mkdir(parents=True)
        (case_dir / "tmt_failed").write_text("", encoding="utf-8")

        collect_report.collect_data()

        assert collect_report.full_success is False
        assert collect_report.data_dict["tmt"]["tmt_failed"] == ["fedora-test"]
        assert "fedora-test" not in collect_report.data_dict["SUCCESS"]
