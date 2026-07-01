import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def write_dictionary() -> Path:
    """Writes the data dictionary to `src/feasibility_data/metadata/redcap/dictionary.json`."""
    data_dict = _request_dictionary()
    file_path = (
        Path("src") / "feasibility_data" / "metadata" / "redcap" / "dictionary.json"
    )
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)
    return file_path


def _request_dictionary() -> list[dict[str, str]]:
    """Gets the data dictionary from REDCap."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "metadata",
        "format": "json",
        "returnFormat": "json",
    }
    response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    dictionary: list[dict[str, str]] = response.json()
    return dictionary
