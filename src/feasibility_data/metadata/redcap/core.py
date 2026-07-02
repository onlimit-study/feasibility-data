from pathlib import Path

from feasibility_data.common.redcap.api import get_json_from_redcap
from feasibility_data.common.redcap.json import write_json


def download_redcap_metadata(path: Path, content: str) -> None:
    """Download data from REDCap and save it to a JSON file."""
    data = get_json_from_redcap(content)
    write_json(path, data)


def expand_checkbox_fields(
    field_metadata_preprocessed_path: Path, field_metadata_path: Path
) -> None:
    """Expand checkbox fields in the field metadata.

    Checkbox fields are listed in the data using a separate column for each option.
    To be able to match fields and forms in the data based on the field metadata,
    checkbox fields are first expanded into a representation matching the data.
    E.g.: treatment_v0 -> treatment_v0___1, treatment_v0___2, treatment_v0___3
    """
    ...
