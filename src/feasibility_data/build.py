from importlib.resources import files
from pathlib import Path
from typing import Annotated

from pytask import DirectoryNode, Product

import feasibility_data.common.json as cj
import feasibility_data.common.redcap as cr
import feasibility_data.data.myfood24.raw as dmr
import feasibility_data.data.redcap.raw as dr
from feasibility_data.common import dotenv

dotenv.load_env_vars()

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()
RAW = SRC.joinpath("..", "raw").resolve()

BLD_REDCAP = BLD / "redcap"
RAW_REDCAP = RAW / "redcap"

RAW_MYFOOD24 = RAW / "myfood24"

FIELD_METADATA_PATH = BLD_REDCAP / "field_metadata.json"


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = FIELD_METADATA_PATH,
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    metadata = cr.get_json("metadata")
    cj.write_json(field_metadata_path, metadata)


def task_download_myfood24_data(
    myfood24_raw_data_dir: Annotated[
        Path,
        DirectoryNode(root_dir=RAW_MYFOOD24, pattern="*.zip"),
        Product,
    ],
) -> None:
    """Download the myfood24 data."""
    data = dmr.download()
    dmr.write(data, myfood24_raw_data_dir)


def task_download_raw_redcap_data(
    raw_data_dir: Annotated[
        Path,
        DirectoryNode(root_dir=RAW_REDCAP, pattern="*.csv.gz"),
        Product,
    ],
) -> None:
    """Download the latest data from all centers to `RAW_REDCAP/<timestamp>.csv.gz`."""
    # TODO: Handle all centers
    for center in [cr.Center.Copenhagen]:
        data = dr.download_data(center)
        dr.write_data(data, raw_data_dir)
