from importlib.resources import files
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pytask import DirectoryNode, Product

import feasibility_data.common.json as cj
import feasibility_data.common.redcap as cr
import feasibility_data.data.myfood24.raw as dmr
import feasibility_data.data.redcap.raw as dr
import feasibility_data.metadata.redcap.core as mrc

load_dotenv()

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()
RAW = SRC.joinpath("..", "raw").resolve()

BLD_REDCAP = BLD / "redcap"
RAW_REDCAP = RAW / "redcap"

RAW_MYFOOD24 = RAW / "myfood24"

FIELD_METADATA_PATH = BLD_REDCAP / "field_metadata.json"
EVENT_METADATA_PATH = BLD_REDCAP / "event_metadata.json"
REPEATING_FORMS_METADATA_PATH = BLD_REDCAP / "repeating_forms_metadata.json"
FIELD_METADATA_PREPROCESSED_PATH = BLD_REDCAP / "field_metadata_preprocessed.json"


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
