from importlib.resources import files
from pathlib import Path
from typing import Annotated

from pytask import Product

import feasibility_data.common.json as cj
import feasibility_data.common.redcap as cr

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()

BLD_REDCAP = BLD / "redcap"

FIELD_METADATA_PATH = BLD_REDCAP / "field_metadata.json"


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = FIELD_METADATA_PATH,
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    metadata = cr.get_json("metadata")
    cj.write_json(field_metadata_path, metadata)
