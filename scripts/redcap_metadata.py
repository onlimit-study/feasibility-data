import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def get_data_dict_from_redcap() -> list[dict[str, str]]:
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
    return response.json()


def get_form_event_mapping_from_redcap() -> list[dict[str, str]]:
    """Gets the form-event mapping from REDCap."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "formEventMapping",
        "format": "json",
        "returnFormat": "json",
    }
    response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def get_repeating_instruments_from_redcap() -> list[dict[str, str]]:
    """Gets repeating instruments from REDCap."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "repeatingFormsEvents",
        "format": "json",
        "returnFormat": "json",
    }
    response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def save_metadata():
    """Saves the data dictionary and repeating instruments in the `scripts` folder."""
    data_dict = get_data_dict_from_redcap()
    data_dict_path = Path("scripts") / "data_dictionary.json"
    data_dict_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_dict_path, "w") as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)

    form_event_mapping = get_form_event_mapping_from_redcap()
    form_event_mapping_path = Path("scripts") / "form_event.json"
    with open(form_event_mapping_path, "w") as f:
        json.dump(form_event_mapping, f, indent=2, ensure_ascii=False)

    repeating_instruments = get_repeating_instruments_from_redcap()
    repeating_instruments_path = Path("scripts") / "repeating_instruments.json"
    with open(repeating_instruments_path, "w") as f:
        json.dump(repeating_instruments, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    save_metadata()
