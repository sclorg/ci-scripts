# pylint: disable=import-error,redefined-outer-name
import sys
import pytest

from pathlib import Path
from unittest.mock import MagicMock, patch

from daily_tests import download_logs


TEST_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(TEST_DIR.parent))


@pytest.fixture
def tmp_log_dir(tmp_path):
    """Set up SHARED_DIR and return the path for test isolation."""
    with patch.dict("os.environ", {"SHARED_DIR": str(tmp_path)}):
        with patch.object(download_logs, "LOG_DIR", str(tmp_path)):
            yield tmp_path


@pytest.fixture
def log_file_with_request_id(tmp_path):
    """Create a log file containing a Testing Farm request ID."""
    log_file = tmp_path / "test.log"
    log_file.write_text(
        "some line\n"
        "api https://api.dev.testing-farm.io/v0.1/requests/abc-123-def/status\n"
        "another line\n"
    )
    return str(log_file)


@pytest.fixture
def log_file_without_request_id(tmp_path):
    """Create a log file without a request ID."""
    log_file = tmp_path / "test.log"
    log_file.write_text("some line\nno request id here\n")
    return str(log_file)


@pytest.fixture
def downloader(tmp_log_dir, log_file_with_request_id):
    """Create a TestingFarmLogDownloader instance with valid log file."""
    return download_logs.TestingFarmLogDownloader(
        log_file_with_request_id, "fedora", "test-pytest"
    )


class TestTestingFarmLogDownloaderInit:
    """Tests for TestingFarmLogDownloader.__init__."""

    def test_init_sets_attributes(self, tmp_log_dir, log_file_with_request_id):
        downloader = download_logs.TestingFarmLogDownloader(
            log_file_with_request_id, "c9s", "test"
        )
        assert downloader.log_file == Path(log_file_with_request_id)
        assert downloader.target == "c9s"
        assert downloader.test == "test"
        assert downloader.request_id is None
        assert downloader.xml_dict is None
        assert downloader.data_dir_url_link is None
        assert "daily_reports_dir" in str(downloader.log_dir)
        assert "c9s-test" in str(downloader.log_dir)


class TestGetRequestId:
    """Tests for TestingFarmLogDownloader.get_request_id."""

    def test_get_request_id_success(self, downloader, capsys):
        result = downloader.get_request_id()
        assert result is True
        assert downloader.request_id == "abc-123-def"
        assert "Request ID: abc-123-def" in capsys.readouterr().out

    def test_get_request_id_failure(
        self, tmp_log_dir, log_file_without_request_id, capsys
    ):
        downloader = download_logs.TestingFarmLogDownloader(
            log_file_without_request_id, "fedora", "test"
        )
        result = downloader.get_request_id()
        assert result is False
        assert downloader.request_id is None
        assert "Request ID not found" in capsys.readouterr().out


class TestDownloadLog:
    """Tests for TestingFarmLogDownloader.download_log."""

    def test_download_log_success(self, downloader, tmp_path):
        downloader.log_dir = tmp_path
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"log content"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            result = downloader.download_log("http://example.com/log.txt", "log.txt")

        assert result is True
        assert (tmp_path / "log.txt").read_bytes() == b"log content"

    def test_download_log_success_failed_dir(self, downloader, tmp_path):
        (tmp_path / "results").mkdir()
        downloader.log_dir = tmp_path
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"failed log"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            result = downloader.download_log(
                "http://example.com/fail.log", "fail.log", is_failed=True
            )

        assert result is True
        assert (tmp_path / "results" / "fail.log").read_bytes() == b"failed log"

    def test_download_log_failure_after_retries(self, downloader, tmp_path, capsys):
        downloader.log_dir = tmp_path
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            with patch("daily_tests.download_logs.time.sleep"):
                result = downloader.download_log(
                    "http://example.com/missing.log", "missing.log"
                )

        assert result is False
        assert "Failed to download log" in capsys.readouterr().out


class TestDownloadTmtLogs:
    """Tests for TestingFarmLogDownloader.download_tmt_logs."""

    def test_download_tmt_logs_no_xml_dict(self, downloader, capsys):
        downloader.xml_dict = None
        result = downloader.download_tmt_logs()
        assert result is False
        assert "XML report not found" in capsys.readouterr().out

    def test_download_tmt_logs_downloads_logs_and_sets_data_link(
        self, downloader, tmp_path
    ):
        downloader.log_dir = tmp_path
        downloader.xml_dict = {
            "testsuites": {
                "testsuite": {
                    "logs": {
                        "log": [
                            {"@name": "tmt-log", "@href": "http://example.com/tmt.log"},
                            {
                                "@name": "tmt-verbose-log",
                                "@href": "http://example.com/tmt-verbose.log",
                            },
                            {"@name": "data", "@href": "http://example.com/data"},
                        ]
                    }
                }
            }
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"log content"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            downloader.download_tmt_logs()

        assert downloader.data_dir_url_link == "http://example.com/data"
        assert (tmp_path / "tmt-log").read_bytes() == b"log content"
        assert (tmp_path / "tmt-verbose-log").read_bytes() == b"log content"


class TestGetListOfContainersLogs:
    """Tests for TestingFarmLogDownloader.get_list_of_containers_logs."""

    def test_get_list_of_containers_logs_finds_links(self, downloader):
        html = '<a href="httpd-container">\n<a href="nginx-container">\n'
        result = downloader.get_list_of_containers_logs(html)
        assert result == ['<a href="httpd-container">', '<a href="nginx-container">']

    def test_get_list_of_containers_logs_empty(self, downloader):
        result = downloader.get_list_of_containers_logs("no links here")
        assert result == []

    def test_get_list_of_containers_logs_exception(self, downloader, capsys):
        with patch.object(download_logs, "re") as mock_re:
            mock_re.search.side_effect = Exception("regex error")
            result = downloader.get_list_of_containers_logs("html")
        assert result is False
        assert "Failed to get list of failed containers" in capsys.readouterr().out


class TestDownloadContainerLogs:
    """Tests for TestingFarmLogDownloader.download_container_logs."""

    def test_download_container_logs_no_data_link(self, downloader, capsys):
        downloader.data_dir_url_link = None
        result = downloader.download_container_logs()
        assert result is False
        assert "Data directory URL link not found" in capsys.readouterr().out

    def test_download_container_logs_success(self, downloader, tmp_path):
        downloader.log_dir = tmp_path
        downloader.data_dir_url_link = "http://example.com/data"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>data dir</html>"
        mock_response.content = b"log"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            result = downloader.download_container_logs()

        assert result is True

    def test_download_container_logs_failed_directory(self, downloader, tmp_path):
        (tmp_path / "results").mkdir()
        downloader.log_dir = tmp_path
        downloader.data_dir_url_link = "http://example.com/data"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>results</html>"
        mock_response.content = b"log"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            result = downloader.download_container_logs(is_failed=True)

        assert result is True

    def test_download_container_logs_http_error(self, downloader, capsys):
        downloader.data_dir_url_link = "http://example.com/data"
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            result = downloader.download_container_logs()

        assert result is False
        assert "Failed to download data" in capsys.readouterr().out


class TestGetXmlReport:
    """Tests for TestingFarmLogDownloader.get_xml_report."""

    def test_get_xml_report_public_url_for_fedora(self, downloader, capsys):
        downloader.request_id = "req-123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<testsuites></testsuites>"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            with patch(
                "daily_tests.download_logs.xmltodict.parse",
                return_value={"testsuites": {}},
            ):
                result = downloader.get_xml_report()

        assert result is True
        assert downloader.xml_dict == {"testsuites": {}}
        assert "artifacts.dev.testing-farm.io" in capsys.readouterr().out

    def test_get_xml_report_public_url_for_c9s(
        self, tmp_log_dir, log_file_with_request_id
    ):
        downloader = download_logs.TestingFarmLogDownloader(
            log_file_with_request_id, "c9s", "test"
        )
        downloader.get_request_id()
        downloader.request_id = "req-456"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<testsuites></testsuites>"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            with patch(
                "daily_tests.download_logs.xmltodict.parse",
                return_value={"testsuites": {}},
            ):
                result = downloader.get_xml_report()

        assert result is True

    def test_get_xml_report_private_url_for_rhel(
        self, tmp_log_dir, log_file_with_request_id
    ):
        downloader = download_logs.TestingFarmLogDownloader(
            log_file_with_request_id, "rhel9", "test"
        )
        downloader.get_request_id()
        downloader.request_id = "req-789"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<testsuites></testsuites>"

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ) as mock_get:
            with patch(
                "daily_tests.download_logs.xmltodict.parse",
                return_value={"testsuites": {}},
            ):
                result = downloader.get_xml_report()

        assert result is True
        assert "artifacts.osci.redhat.com" in str(mock_get.call_args[0][0])

    def test_get_xml_report_failure_after_retries(self, downloader, capsys):
        downloader.request_id = "req-123"
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch(
            "daily_tests.download_logs.requests.get", return_value=mock_response
        ):
            with patch("daily_tests.download_logs.time.sleep"):
                result = downloader.get_xml_report()

        assert result is False
        assert downloader.xml_dict is None
        assert "Failed to download XML report" in capsys.readouterr().out
