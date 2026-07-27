from importlib.resources import files
from pathlib import Path
from typing import Annotated

from pytask import Product

import feasibility_data.common.json as cj
import feasibility_data.common.redcap as cr
import feasibility_data.metadata.redcap.core as mrc

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()

BLD_REDCAP = BLD / "redcap"

FIELD_METADATA_PATH = BLD_REDCAP / "field_metadata.json"
FIELD_METADATA_PREPROCESSED_PATH = BLD_REDCAP / "field_metadata_preprocessed.json"


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = FIELD_METADATA_PATH,
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    metadata = cr.get_json("metadata")
    cj.write_json(field_metadata_path, metadata)


def task_preprocess_field_metadata(
    field_metadata_preprocessed_path: Annotated[
        Path, Product
    ] = FIELD_METADATA_PREPROCESSED_PATH,
    field_metadata_path: Path = FIELD_METADATA_PATH,
) -> None:
    """Preprocess field metadata."""
    field_metadata = cj.read_json(field_metadata_path)
    field_metadata_preprocessed = mrc.expand_checkbox_fields(field_metadata)
    cj.write_json(field_metadata_preprocessed_path, field_metadata_preprocessed)
