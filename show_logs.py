#!/usr/bin/env python3
import os
import sys

from pathlib import Path

DAILY_REPORTS_DIR = Path("/var/ci-scripts/daily_reports_dir/")
DAILY_SCL_TESTS_DIR = Path("/var/ci-scripts/daily_scl_tests/")


class PVCWatcherReport:
    def __init__(self):
        self.cwd = os.getcwd()

    def iter_results_in_directory(self):
        """Yield all files in the given directory."""
        success_tests = []
        failed_tests = []
        for item in DAILY_REPORTS_DIR.iterdir():
            print(f"Inspecting item: {item}")
            if item.is_dir():
                if (item / "tmt_success").exists():
                    success_tests.append(item.name)
                else:
                    failed_tests.append(item.name)
        print(f"Success tests in {DAILY_REPORTS_DIR} are: {success_tests}")
        print(f"Failed tests in {DAILY_REPORTS_DIR} are: {failed_tests}")

    def iter_over_executed_tests(self):
        """Yield all executed tests in the given directory."""
        executed_tests = []
        for item in DAILY_SCL_TESTS_DIR.iterdir():
            print(f"Inspecting item: {item}")
            if item.is_file():
                executed_tests.append(item.name)
        print("Executed tests are:")
        print(executed_tests.split("\n"))

    def print_report(self):
        print("Daily SCL Tests Reports:")
        self.iter_over_executed_tests()
        self.iter_results_in_directory()


if __name__ == "__main__":
    dgr = PVCWatcherReport()
    dgr.print_report()
    sys.exit(0)
