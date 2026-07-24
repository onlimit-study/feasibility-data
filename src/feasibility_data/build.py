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
EVENT_METADATA_PATH = BLD_REDCAP / "event_metadata.json"
REPEATING_FORMS_METADATA_PATH = BLD_REDCAP / "repeating_forms_metadata.json"


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = FIELD_METADATA_PATH,
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    metadata = cr.get_json("metadata")
    cj.write_json(field_metadata_path, metadata)


def task_download_event_metadata(
    event_metadata_path: Annotated[Path, Product] = EVENT_METADATA_PATH,
) -> None:
    """Download event metadata to `BLD_REDCAP`."""
    metadata = cr.get_json("formEventMapping")
    cj.write_json(event_metadata_path, metadata)


def task_download_repeating_forms_metadata(
    repeating_forms_metadata_path: Annotated[
        Path, Product
    ] = REPEATING_FORMS_METADATA_PATH,
) -> None:
    """Download repeating forms metadata to `BLD_REDCAP`."""
    metadata = cr.get_json("repeatingFormsEvents")
    cj.write_json(repeating_forms_metadata_path, metadata)
