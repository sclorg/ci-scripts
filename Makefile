.PHONY: run_daily_tests shellcheck

run_daily_tests:
	bash daily_tests/daily_scl_tests.sh

shellcheck:
	./run-shellcheck.sh `git ls-files *.sh`
