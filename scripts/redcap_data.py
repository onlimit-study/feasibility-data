import gzip
import json
import os
from datetime import datetime
from operator import itemgetter
from pathlib import Path

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


def get_instrument_data_from_redcap(instrument: str) -> list[dict[str, str]]:
    """Gets the data for a specific instrument from REDCap as JSON."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "record",
        "action": "export",
        "format": "json",
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
    return response.json()


def save_instrument_data(instrument: str):
    """Saves instrument data to `raw/redcap/<instrument>/<timestamp>.json.gz`."""
    data = get_instrument_data_from_redcap(instrument)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    file_path = Path("raw") / "redcap" / instrument / f"{timestamp}.json.gz"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    instruments = get_instruments()
    so.pretty_print(f"Found {len(instruments)} instruments.")

    for instrument in instruments:
        save_instrument_data(instrument)
        so.pretty_print(f"Saved data for instrument: {instrument!r}.")
