from io import StringIO
from pathlib import Path

import polars as pl

from feasibility_data import common


def download(center: common.redcap.Center) -> str:
    """Download the data."""
    return common.redcap.get(
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


def write(data: str, raw_data_dir: Path) -> None:
    """Write the data as a timestamped file."""
    df = pl.read_csv(StringIO(data), separator=";", infer_schema=False)
    data_path = raw_data_dir / f"{common.datetime.get_current()}.csv.gz"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    df.write_csv(data_path, compression="gzip")
