import csv
import os
from pathlib import Path

from locust.env import Environment, MasterRunner
from locust.html import get_html_report
from locust.stats import StatsCSV, PERCENTILES_TO_REPORT

from src.olaf.s3_uploader import upload_session_dir


def add_session_dir_arg(parser):
    parser.add_argument("--session_dir", type=str, default="", help="path to session directory")


def on_test_quit(environment: Environment, **kwargs):
    if isinstance(environment.runner, MasterRunner):
        session_path = Path(environment.parsed_options.session_dir)
        html_report = get_html_report(environment, show_download_link=False)
        with open(os.path.join(session_path, "report.html"), mode="w", encoding="utf-8") as f:
            f.write(html_report)

        stats = StatsCSV(environment, percentiles_to_report=PERCENTILES_TO_REPORT)
        with open(os.path.join(session_path, "csv_summary.csv"), "w") as f:
            stats.requests_csv(csv.writer(f))

        with open(os.path.join(session_path, "csv_exception.csv"), "w") as f:
            stats.exceptions_csv(csv.writer(f))

        with open(os.path.join(session_path, "csv_failures.csv"), "w") as f:
            stats.failures_csv(csv.writer(f))

        upload_session_dir(session_path)
