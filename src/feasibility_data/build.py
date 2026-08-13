from importlib.resources import files
from pathlib import Path
from typing import Annotated

import polars as pl
import seedcase_soil as so
from pytask import DirectoryNode, Product

from feasibility_data import common, data, metadata

common.dotenv.load_env_vars()

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()
RAW = SRC.joinpath("..", "raw").resolve()

BLD_REDCAP = BLD / "redcap"
RAW_REDCAP = RAW / "redcap"
RAW_REDCAP_DATA = DirectoryNode(root_dir=RAW_REDCAP, pattern="*.csv.gz")

RAW_MYFOOD24 = RAW / "myfood24"

FIELD_METADATA_PATH = BLD_REDCAP / "field_metadata.json"
EVENT_METADATA_PATH = BLD_REDCAP / "event_metadata.json"
REPEATING_FORMS_METADATA_PATH = BLD_REDCAP / "repeating_forms_metadata.json"
FORM_METADATA_PATH = BLD_REDCAP / "form_metadata.json"
FORMS = BLD_REDCAP / "forms"


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = FIELD_METADATA_PATH,
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    metadata = common.redcap.get_json("metadata")
    common.json.write(field_metadata_path, metadata)


def task_download_event_metadata(
    event_metadata_path: Annotated[Path, Product] = EVENT_METADATA_PATH,
) -> None:
    """Download event metadata to `BLD_REDCAP`."""
    metadata = common.redcap.get_json("formEventMapping")
    common.json.write(event_metadata_path, metadata)


def task_download_repeating_forms_metadata(
    repeating_forms_metadata_path: Annotated[
        Path, Product
    ] = REPEATING_FORMS_METADATA_PATH,
) -> None:
    """Download repeating forms metadata to `BLD_REDCAP`."""
    metadata = common.redcap.get_json("repeatingFormsEvents")
    common.json.write(repeating_forms_metadata_path, metadata)


def task_download_raw_redcap_data(
    raw_data_dir: Annotated[Path, RAW_REDCAP_DATA, Product],
) -> None:
    """Download the latest data from all centers to `RAW_REDCAP/<timestamp>.csv.gz`."""
    # TODO: Handle all centers
    for center in [common.redcap.Center.Copenhagen]:
        csv_data = data.redcap.raw.download(center)
        data.redcap.raw.write(csv_data, raw_data_dir)


def task_create_form_metadata(
    form_metadata_path: Annotated[Path, Product] = FORM_METADATA_PATH,
    field_metadata_path: Path = FIELD_METADATA_PATH,
    event_metadata_path: Path = EVENT_METADATA_PATH,
    repeating_forms_path: Path = REPEATING_FORMS_METADATA_PATH,
) -> None:
    """Create the metadata file describing each form."""
    event_metadata = pl.read_json(event_metadata_path)
    repeating_forms_metadata = pl.read_json(repeating_forms_path)
    field_metadata = common.json.read(field_metadata_path)
    field_metadata = metadata.redcap.core.expand_checkbox_fields(field_metadata)

    form_metadata = metadata.redcap.core.create_form_metadata(
        pl.DataFrame(field_metadata),
        event_metadata,
        repeating_forms_metadata,
    )

    common.json.write(form_metadata_path, form_metadata)


def task_split_forms(
    forms_dir: Annotated[
        Path,
        DirectoryNode(root_dir=FORMS, pattern="**/*.parquet"),
        Product,
    ],
    raw_data_paths: Annotated[list[Path], RAW_REDCAP_DATA],
    form_metadata_path: Path = FORM_METADATA_PATH,
) -> None:
    """Split each batch of raw data into one Parquet file per form.

    Written to `FORMS/<timestamp>/<form_name>.parquet`.
    """
    forms_metadata = so.fmap(
        common.json.read(form_metadata_path),
        lambda item: metadata.redcap.core.FormMetadata(**item),
    )
    for raw_data_path in raw_data_paths:
        raw_data = data.redcap.core.read_raw(raw_data_path, forms_metadata)
        forms = data.redcap.core.split_forms(raw_data, forms_metadata)

        for form in forms:
            data.redcap.core.write_form(form, forms_dir, raw_data_path)


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
