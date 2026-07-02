import os
from datetime import datetime
from io import StringIO
from pathlib import Path

import polars as pl
import requests
import seedcase_soil as so
from dotenv import load_dotenv

load_dotenv()


def write_raw() -> Path:
    """Writes the raw data to `raw/redcap/<timestamp>.csv.gz`."""
    data = _request_raw()
    df = pl.read_csv(StringIO(data), separator=";", infer_schema=False)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    file_path = Path("raw") / "redcap" / f"{timestamp}.csv.gz"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(file_path, compression="gzip")
    so.pretty_print(f"Saved data to '{file_path}'.")
    return file_path


def _request_raw() -> str:
    """Gets the data from REDCap as CSV."""
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
    response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=60)
    response.raise_for_status()
    return response.text
