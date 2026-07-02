import json
import os
import re
from pathlib import Path
from typing import cast

import requests
import seedcase_soil as so
from dotenv import load_dotenv

load_dotenv()


def download_field_metadata(data_dict_path: Path) -> None:
    """Download field metadata."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "metadata",
        "format": "json",
        "returnFormat": "json",
    }
    # response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=30)
    response = requests.post("https://redcap.au.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    data_dict = response.json()

    data_dict_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_dict_path, "w") as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)


def download_event_metadata(event_metadata_path: Path) -> None:
    """Download event metadata."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "formEventMapping",
        "format": "json",
        "returnFormat": "json",
    }
    # response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=30)
    response = requests.post("https://redcap.au.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    event_metadata = response.json()

    event_metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(event_metadata_path, "w") as f:
        json.dump(event_metadata, f, indent=2, ensure_ascii=False)


def download_repeating_forms(repeating_forms_path: Path) -> None:
    """Download repeating forms."""
    token = os.environ.get("REDC_CPH_API_KEY")
    if not token:
        raise RuntimeError("REDC_CPH_API_KEY environment variable is not set.")

    data = {
        "token": token,
        "content": "repeatingFormsEvents",
        "format": "json",
        "returnFormat": "json",
    }
    # response = requests.post("https://redcap.regionh.dk/api/", data=data, timeout=30)
    response = requests.post("https://redcap.au.dk/api/", data=data, timeout=30)
    response.raise_for_status()
    repeating_forms = response.json()

    repeating_forms_path.parent.mkdir(parents=True, exist_ok=True)
    with open(repeating_forms_path, "w") as f:
        json.dump(repeating_forms, f, indent=2, ensure_ascii=False)


def expand_checkbox_fields(
    field_metadata_preprocessed_path: Path, field_metadata_path: Path
) -> None:
    """Expand checkbox fields in the field metadata."""
    with open(field_metadata_path) as f:
        field_metadata = json.load(f)

    checkbox_fields = so.keep(
        field_metadata, lambda field: field["field_type"] == "checkbox"
    )
    non_checkbox_fields = so.keep(
        field_metadata, lambda field: field["field_type"] != "checkbox"
    )
    expanded_choice_fields = so.flat_fmap(checkbox_fields, _expand_checkbox_field)

    field_metadata_preprocessed = non_checkbox_fields + expanded_choice_fields
    with open(field_metadata_preprocessed_path, "w") as f:
        json.dump(field_metadata_preprocessed, f, indent=2, ensure_ascii=False)


def _expand_checkbox_field(checkbox_field: dict[str, str]) -> list[dict[str, str]]:
    return so.fmap(
        _get_choices(checkbox_field),
        lambda choice: (
            checkbox_field
            | {
                "field_name": f"{checkbox_field['field_name']}___{choice[0]}",
                "field_label": choice[1],
            }
        ),
    )


def _get_choices(field: dict[str, str]) -> list[tuple[str, str]]:
    """Parses the choices into the choice number and choice value.

    E.g.:
        Input: "1, first choice|2, second choice|3, third choice"
        Output: [('1', 'first choice'), ('2', 'second choice'), ('3', 'third choice')]
    """
    choices = field["select_choices_or_calculations"].split("|")
    matches = so.fmap(
        choices, lambda choice: re.match(r"^(\d+), *(.*)", choice.strip())
    )
    if not all(matches):
        raise ValueError(_get_error_message(field, "select_choices_or_calculations"))
    return so.fmap(
        cast(list[re.Match], matches),
        lambda match: (match.group(1), match.group(2)),
    )


def _get_error_message(field: dict[str, str], key: str) -> str:
    return (
        f"Unexpected value {field[key]!r} for `{key}` in field {field['field_name']!r} "
        f"in form {field['form_name']!r}."
    )
