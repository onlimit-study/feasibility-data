from pathlib import Path

from feasibility_data.common.redcap.api import get_json_from_redcap
from feasibility_data.common.redcap.json import write_json


def download_redcap_metadata(path: Path, content: str) -> None:
    """Download data from REDCap and save it to a JSON file."""
    data = get_json_from_redcap(content)
    write_json(path, data)
