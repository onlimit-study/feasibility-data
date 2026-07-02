from importlib.resources import files
from pathlib import Path
from typing import Annotated

from pytask import DirectoryNode, Product

from feasibility_data.common.redcap.api import Center
from feasibility_data.data.redcap.core import (
    group_forms_by_resource,
    split_forms,
    stage_other_resources,
)
from feasibility_data.data.redcap.raw import download_redcap_data
from feasibility_data.data.redcap.vas import stage_vas
from feasibility_data.metadata.redcap.core import (
    download_redcap_metadata,
    expand_checkbox_fields,
)

SRC = Path(str(files("feasibility_data"))).joinpath("..").resolve()
BLD = SRC.joinpath("..", "bld").resolve()
RAW = SRC.joinpath("..", "raw").resolve()
STAGING = SRC.joinpath("..", "staging").resolve()

BLD_REDCAP = BLD / "redcap"
RAW_REDCAP = RAW / "redcap"
STAGING_REDCAP = STAGING / "redcap"


def task_download_data(
    raw_data_dir: Annotated[
        Path,
        DirectoryNode(root_dir=RAW_REDCAP, pattern="*.csv.gz"),
        Product,
    ],
) -> None:
    """Download the latest data from all centers to `RAW_REDCAP/<timestamp>.csv.gz`."""
    for center in [Center.Copenhagen]:
        download_redcap_data(raw_data_dir, center)


def task_download_event_metadata(
    event_metadata_path: Annotated[Path, Product] = BLD_REDCAP / "event_metadata.json",
) -> None:
    """Download event metadata to `BLD_REDCAP`."""
    download_redcap_metadata(event_metadata_path, "formEventMapping")


def task_download_repeating_forms(
    repeating_forms_path: Annotated[Path, Product] = BLD_REDCAP
    / "repeating_forms.json",
) -> None:
    """Download repeating forms to `BLD_REDCAP`."""
    download_redcap_metadata(repeating_forms_path, "repeatingFormsEvents")


def task_download_field_metadata(
    field_metadata_path: Annotated[Path, Product] = BLD_REDCAP / "field_metadata.json",
) -> None:
    """Download field metadata to `BLD_REDCAP`."""
    download_redcap_metadata(field_metadata_path, "metadata")


def task_preprocess_field_metadata(
    field_metadata_preprocessed_path: Annotated[Path, Product] = BLD_REDCAP
    / "field_metadata_preprocessed.json",
    field_metadata_path: Path = BLD_REDCAP / "field_metadata.json",
) -> None:
    """Preprocess field metadata."""
    expand_checkbox_fields(field_metadata_preprocessed_path, field_metadata_path)


def task_split_forms(
    forms_dir: Annotated[
        Path,
        DirectoryNode(root_dir=BLD_REDCAP / "forms", pattern="**/*.parquet"),
        Product,
    ],
    raw_data_paths: Annotated[
        list[Path], DirectoryNode(root_dir=RAW_REDCAP, pattern="*.csv.gz")
    ],
    field_metadata_path: Path = BLD_REDCAP / "field_metadata_preprocessed.json",
    event_metadata_path: Path = BLD_REDCAP / "event_metadata.json",
    repeating_forms_path: Path = BLD_REDCAP / "repeating_forms.json",
) -> None:
    """Split each batch of raw data into one Parquet file per form.

    Written to `BLD_REDCAP/forms/<timestamp>/<form_name>.parquet`.
    """
    for raw_data_path in raw_data_paths:
        split_forms(
            forms_dir,
            raw_data_path,
            field_metadata_path,
            event_metadata_path,
            repeating_forms_path,
        )


def task_stage_resources(
    staging_dir: Annotated[
        Path,
        DirectoryNode(root_dir=STAGING_REDCAP, pattern="**/*.parquet"),
        Product,
    ],
    form_paths: Annotated[
        list[Path],
        DirectoryNode(root_dir=BLD_REDCAP / "forms", pattern="**/*.parquet"),
    ],
    # Possibly other dependencies
) -> None:
    """Stage split forms as resources in the `staging` folder.

    Written to `STAGING_REDCAP/<resource_name>/<timestamp>.parquet`.
    """
    forms_by_resource = group_forms_by_resource(form_paths)
    stage_vas(staging_dir, forms_by_resource["vas"])
    ...
    stage_other_resources(staging_dir, forms_by_resource["other"])
