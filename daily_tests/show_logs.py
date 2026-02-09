#!/usr/bin/env python3
import os
import sys

from datetime import date
from pathlib import Path

DAILY_REPORTS_DIR = Path("/var/ci-scripts/daily_reports_dir/")
DAILY_SCL_TESTS_DIR = Path("/var/ci-scripts/daily_scl_tests/")

TEST_CASES = {
    # Format is test for OS and king of test, what TMT Plan is used and MSG to mail
    ("c10s", "nightly/nightly-c10s"),
    ("fedora", "nightly/nightly-fedora"),
    ("c9s", "nightly/nightly-c9s"),
    ("rhel8", "nightly/nightly-rhel8"),
    ("rhel9", "nightly/nightly-rhel9"),
    ("rhel10", "nightly/nightly-rhel10"),
}


class PVCWatcherReport:
    def __init__(self):
        self.cwd = os.getcwd()
        self.date = date.today().strftime("%Y-%m-%d")
        self.reports_dir = DAILY_REPORTS_DIR / self.date
        self.scl_tests_dir = DAILY_SCL_TESTS_DIR / self.date

    def iter_results_in_directory(self):
        success_tmt_plans = []
        failed_tmt_plans = []
        running_tmt_plans = []
        failed_container_tests = []
        print("Show status of all TMT/FMF plans:")
        if self.scl_tests_dir.is_dir():
            for item in self.scl_tests_dir.iterdir():
                if not item.is_dir():
                    continue
                if (self.scl_tests_dir / item.name / "tmt_running").exists():
                    running_tmt_plans.append(item.name)
        if self.reports_dir.is_dir():
            for item in self.reports_dir.iterdir():
                item_dir = self.reports_dir / item.name
                print(f"Going throw {item_dir}")
                if not item_dir.is_dir():
                    continue
                if (item_dir / "tmt_success").exists():
                    success_tmt_plans.append(item.name)
                else:
                    failed_tmt_plans.append(item.name)
                failed_container_tests.extend(self.return_failed_tests(item_dir, item))
        if running_tmt_plans:
            print("Running TMT plans that are not finished yet:")
            print("\n".join(running_tmt_plans))
        if success_tmt_plans:
            print(f"Success TMT plans in {self.reports_dir} are:")
            print("\n".join(success_tmt_plans))
        if failed_tmt_plans:
            print(f"Failed TMT plans in {self.reports_dir} are:")
            print("\n".join(failed_tmt_plans))
        if failed_container_tests:
            print(f"!!!!Failed container tests are: {failed_container_tests}!!!!")

    def return_failed_tests(self, directory, item) -> list:
        plan_name = "".join([x[1] for x in TEST_CASES if item.name.startswith(x[0])])
        dir_path = directory / f"{item.name}/plans/{plan_name}/data/results"
        print(f"Looking for failed tests in directory: {dir_path}")
        return list(dir_path.rglob("*.log"))

    def iter_over_executed_tests(self):
        """View all executed tests in the given directory."""
        for item in self.scl_tests_dir.iterdir():
            print(f"Inspecting item in '{self.scl_tests_dir}' directory: {item}")
            item_dir = self.scl_tests_dir / item.name
            if not item_dir.is_dir():
                continue
            failed_container_tests = self.return_failed_tests(item_dir, item)
            if not failed_container_tests:
                print(f"No container test failures found in {item}.")
                continue
            print(f"!!!!Failed container tests for {item.name}!!!!\n")
            print({"\n".join(failed_container_tests)})

    def show_all_available_tests(self):
        print("All previous available tests are:")
        for item in DAILY_REPORTS_DIR.iterdir():
            if item.is_dir():
                print(item.name)

    def print_report(self):
        print(f"Summary ({self.date}) of Daily SCL Tests Reports:")
        if not self.scl_tests_dir.is_dir():
            print(
                f"The directory {self.scl_tests_dir} does not exist. Tests were not executed yet."
            )
        else:
            self.iter_over_executed_tests()
        if not self.reports_dir.is_dir():
            print(
                f"The directory {self.reports_dir} does not exist. Tests were not finished yet."
            )
        else:
            print(f"Summary of results reports directory {self.reports_dir}:")
            self.iter_results_in_directory()


if __name__ == "__main__":
    dgr = PVCWatcherReport()
    dgr.show_all_available_tests()
    dgr.print_report()
    sys.exit(0)
