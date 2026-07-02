from importlib.resources import files
from pathlib import Path
from typing import Annotated

from pytask import Product

from feasibility_data.metadata.redcap.core import (
    download_redcap_metadata,
)

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()

BLD_REDCAP = BLD / "redcap"


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = BLD_REDCAP / "field_metadata.json",
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    download_redcap_metadata(field_metadata_path, "metadata")
