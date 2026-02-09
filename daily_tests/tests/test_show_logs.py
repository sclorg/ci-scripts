# pylint: disable=import-error
import sys

from datetime import date as real_date
from pathlib import Path

import pytest


import show_logs

TEST_DIR = Path(__file__).parent.absolute()
sys.path.append(str(TEST_DIR))


class FixedDate(real_date):
    @classmethod
    def today(cls):
        return cls(2024, 1, 2)


@pytest.fixture
def report_env(tmp_path):
    reports_dir = tmp_path / "reports"
    scl_dir = tmp_path / "scl"
    original_reports_dir = show_logs.DAILY_REPORTS_DIR
    original_scl_tests_dir = show_logs.DAILY_SCL_TESTS_DIR
    original_date = show_logs.date
    show_logs.DAILY_REPORTS_DIR = reports_dir
    show_logs.DAILY_SCL_TESTS_DIR = scl_dir
    show_logs.date = FixedDate
    try:
        yield show_logs.PVCWatcherReport(), reports_dir, scl_dir
    finally:
        show_logs.DAILY_REPORTS_DIR = original_reports_dir
        show_logs.DAILY_SCL_TESTS_DIR = original_scl_tests_dir
        show_logs.date = original_date


def test_return_failed_tests_finds_logs(tmp_path):
    item_name = "c9s-example"
    base_dir = tmp_path
    logs_dir = (
        base_dir / item_name / "plans/nightly/nightly-c9s/data/results" / "nested"
    )
    logs_dir.mkdir(parents=True)
    log_file = logs_dir / "failed.log"
    log_file.write_text("failed")

    report = show_logs.PVCWatcherReport()
    results = report.return_failed_tests(base_dir, Path(item_name))

    assert log_file in results


def test_iter_over_executed_tests_no_failures(report_env, capsys):
    report, _, _ = report_env
    report.scl_tests_dir.mkdir(parents=True)
    (report.scl_tests_dir / "c9s-run").mkdir()

    report.iter_over_executed_tests()
    output = capsys.readouterr().out

    assert "No container test failures found in" in output


def test_show_all_available_tests_lists_dirs(report_env, capsys):
    report, reports_dir, _ = report_env
    reports_dir.mkdir()
    (reports_dir / "2024-01-01").mkdir()
    (reports_dir / "2024-01-02").mkdir()
    (reports_dir / "not-a-dir.txt").write_text("skip")

    report.show_all_available_tests()
    output = capsys.readouterr().out

    assert "2024-01-01" in output
    assert "2024-01-02" in output
    assert "not-a-dir.txt" not in output


def test_print_report_missing_directories(report_env, capsys):
    report, _, _ = report_env

    report.print_report()
    output = capsys.readouterr().out

    assert "Tests were not executed yet." in output
    assert "Tests were not finished yet." in output


def test_iter_results_in_directory_summarizes(report_env, capsys):
    report, _, _ = report_env
    report.scl_tests_dir.mkdir(parents=True)
    running_dir = report.scl_tests_dir / "rhel9-test-pytest"
    running_dir.mkdir()
    (running_dir / "tmt_running").write_text("running")

    report.reports_dir.mkdir(parents=True)
    success_dir = report.reports_dir / "c9s-test"
    success_dir.mkdir()
    (success_dir / "tmt_success").write_text("success")

    failed_dir = report.reports_dir / "rhel9-test"
    failed_dir.mkdir()
    failed_log = failed_dir / "plans/nightly/nightly-rhel9/data/results" / "fail.log"
    (failed_dir / "tmt_failed").write_text("failed")
    failed_log.parent.mkdir(parents=True)
    failed_log.write_text("failed")

    report.item_dir = report.reports_dir
    report.iter_results_in_directory()
    output = capsys.readouterr().out

    assert "Running TMT plans" in output
    assert "rhel9-test-pytest" in output
    assert "Success TMT plans" in output
    assert "c9s-test" in output
    assert "Failed TMT plans" in output
    assert "rhel9-test" in output
    assert "Failed container tests" in output
    assert "fail.log" in output
