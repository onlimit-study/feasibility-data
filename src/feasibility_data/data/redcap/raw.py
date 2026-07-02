from datetime import datetime
from io import StringIO
from pathlib import Path

import polars as pl

from feasibility_data.common.redcap.api import Center, get_from_redcap


def download_data(
    raw_data_dir: Path,
    center: Center,
) -> None:
    """Download the data."""
    response = get_from_redcap(
        data={
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
    )
    data = response.text

    df = pl.read_csv(StringIO(data), separator=";", infer_schema=False)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    data_path = raw_data_dir / f"{timestamp}.csv.gz"
    raw_data_dir.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(data_path, compression="gzip")
