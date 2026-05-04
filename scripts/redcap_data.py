import os
from datetime import datetime
from io import StringIO
from operator import itemgetter
from pathlib import Path

import polars as pl
import requests
import seedcase_soil as so
from dotenv import load_dotenv

load_dotenv()


def get_instruments() -> list[str]:
    """Gets the list of instruments from REDCap."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "instrument",
        "format": "json",
        "returnFormat": "json",
    }
    response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    instruments = response.json()
    return so.fmap(instruments, itemgetter("instrument_name"))


def get_instrument_data_from_redcap(instrument: str) -> str:
    """Gets the data for a specific instrument from REDCap as CSV."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "record",
        "action": "export",
        "format": "csv",
        "type": "flat",
        "csvDelimiter": "",
        "forms[0]": instrument,
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


def save_instrument_data(instrument: str):
    """Saves instrument data to `raw-data/redcap/<instrument>/<timestamp>.csv.gz`."""
    data = get_instrument_data_from_redcap(instrument)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    file_path = Path("raw-data") / "redcap" / instrument / f"{timestamp}.csv.gz"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df = pl.read_csv(StringIO(data), infer_schema=False)
    df.write_csv(file_path, compression="gzip")


if __name__ == "__main__":
    instruments = get_instruments()
    so.pretty_print(f"Found {len(instruments)} instruments.")

    for instrument in instruments:
        save_instrument_data(instrument)
        so.pretty_print(f"Saved data for instrument: {instrument!r}.")
