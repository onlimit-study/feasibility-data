from datetime import datetime
from io import StringIO
from pathlib import Path

import polars as pl

import feasibility_data.common.redcap as cr


def download_data(center: cr.Center) -> str:
    """Download the data."""
    return cr.get(
        request_data={
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
        },
        center=center,
    ).text


def write_data(raw_data_dir: Path, data: str) -> None:
    """Write the data as a timestamped file."""
    df = pl.read_csv(StringIO(data), separator=";", infer_schema=False)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    data_path = raw_data_dir / f"{timestamp}.csv.gz"
    raw_data_dir.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(data_path, compression="gzip")
