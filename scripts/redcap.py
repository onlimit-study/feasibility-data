import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def get_data_dict_from_redcap() -> dict[str, str]:
    """Gets the data dictionary from REDCap."""
    token = os.environ.get("REDCAP_TOKEN")
    if not token:
        raise RuntimeError("REDCAP_TOKEN environment variable is not set.")

    data = {
        "token": token,
        "content": "metadata",
        "format": "json",
        "returnFormat": "json",
    }
    response = requests.post("https://redcap.au.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def save_data_dict():
    """Saves the data dictionary from REDCap to `scripts/data_dictionary.json`."""
    data_dict = get_data_dict_from_redcap()
    file_path = Path("scripts") / "data_dictionary.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)
