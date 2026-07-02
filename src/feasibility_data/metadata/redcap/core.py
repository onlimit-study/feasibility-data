import json
import re
from pathlib import Path
from typing import Any, cast

import seedcase_soil as so

from feasibility_data.common.redcap.api import get_json_from_redcap


def download_redcap_metadata(path: Path, content: str) -> None:
    """Download data from REDCap and save it to a JSON file."""
    data = get_json_from_redcap(content)
    _write_json(path, data)


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
    _write_json(field_metadata_preprocessed_path, field_metadata_preprocessed)


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


def _write_json(path: Path, data: Any) -> None:
    """Write data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
