from importlib.resources import files
from pathlib import Path
from typing import Annotated

from pytask import DirectoryNode, Product

from feasibility_data import common, data, metadata

common.dotenv.load_env_vars()

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()
RAW = SRC.joinpath("..", "raw").resolve()

BLD_REDCAP = BLD / "redcap"
RAW_REDCAP = RAW / "redcap"

RAW_MYFOOD24 = RAW / "myfood24"

FIELD_METADATA_PATH = BLD_REDCAP / "field_metadata.json"
FIELD_METADATA_PREPROCESSED_PATH = BLD_REDCAP / "field_metadata_preprocessed.json"


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = FIELD_METADATA_PATH,
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    metadata = common.redcap.get_json("metadata")
    common.json.write(field_metadata_path, metadata)


def task_download_raw_redcap_data(
    raw_data_dir: Annotated[
        Path,
        DirectoryNode(root_dir=RAW_REDCAP, pattern="*.csv.gz"),
        Product,
    ],
) -> None:
    """Download the latest data from all centers to `RAW_REDCAP/<timestamp>.csv.gz`."""
    # TODO: Handle all centers
    for center in [common.redcap.Center.Copenhagen]:
        csv_data = data.redcap.raw.download(center)
        data.redcap.raw.write(csv_data, raw_data_dir)


def task_preprocess_field_metadata(
    field_metadata_preprocessed_path: Annotated[
        Path, Product
    ] = FIELD_METADATA_PREPROCESSED_PATH,
    field_metadata_path: Path = FIELD_METADATA_PATH,
) -> None:
    """Preprocess field metadata."""
    field_metadata = common.json.read(field_metadata_path)
    field_metadata_preprocessed = metadata.redcap.core.expand_checkbox_fields(
        field_metadata
    )
    common.json.write(field_metadata_preprocessed_path, field_metadata_preprocessed)


def task_download_myfood24_data(
    myfood24_raw_data_dir: Annotated[
        Path,
        DirectoryNode(root_dir=RAW_MYFOOD24, pattern="*.zip"),
        Product,
    ],
) -> None:
    """Download the myfood24 data."""
    response = data.myfood24.raw.download()
    data.myfood24.raw.write(response, myfood24_raw_data_dir)
