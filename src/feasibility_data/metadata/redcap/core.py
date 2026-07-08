from pathlib import Path
from typing import Literal

import feasibility_data.common.json as cj
import feasibility_data.common.redcap as cr


def download_redcap_metadata(
    path: Path,
    content: Literal["metadata", "repeatingFormsEvents", "formEventMapping"],
) -> None:
    """Download data from REDCap and save it to a JSON file."""
    data = cr.get_json(content)
    cj.write_json(path, data)
