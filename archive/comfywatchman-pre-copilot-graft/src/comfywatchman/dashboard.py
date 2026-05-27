"""Generate a static HTML dashboard from the master status report."""

import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from .config import config
from .utils import load_json_file


def generate_dashboard():
    """Generate the HTML dashboard."""
    report_path = config.output_dir / "master_status_report.json"
    report_data = load_json_file(report_path) or {}

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template("dashboard_template.html")

    dashboard_path = config.output_dir / "dashboard.html"

    with open(dashboard_path, "w") as f:
        f.write(template.render(
            workflows=report_data,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    print(f"Dashboard generated at: {dashboard_path}")
