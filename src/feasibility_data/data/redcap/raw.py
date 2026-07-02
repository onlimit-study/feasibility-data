import os
from datetime import datetime
from io import StringIO
from pathlib import Path

import polars as pl
import requests
from dotenv import load_dotenv

load_dotenv()


def download_data(
    raw_data_dir: Path,
) -> None:
    """Download the data."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "record",
        "action": "export",
        "format": "csv",
        "type": "flat",
        "csvDelimiter": ";",
        "rawOrLabel": "raw",
        "rawOrLabelHeaders": "raw",
        "exportCheckboxLabel": "false",
        "exportSurveyFields": "false",
        "exportDataAccessGroups": "false",
        "returnFormat": "json",
    }
    # response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=60)
    response = requests.post("https://redcap.au.dk/api/", data=data, timeout=60)
    response.raise_for_status()

    df = pl.read_csv(StringIO(response.text), separator=";", infer_schema=False)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    data_path = raw_data_dir / f"{timestamp}.csv.gz"
    raw_data_dir.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(data_path, compression="gzip")
