from collections import defaultdict
from pathlib import Path


def split_forms(
    forms_dir: Path,
    raw_data_path: Path,
    field_metadata_path: Path,
    event_metadata_path: Path,
    repeating_forms_path: Path,
) -> None:
    """Split data into one Parquet file per form.

    A new Parquet file is created for each REDCap form, containing only the fields
    belonging to that form and the ID fields.

    The following transformations are done:
      - ID columns are added for all forms.
      - ID column names are standardised.
      - Data provenance is recorded in a `center` column.
      - Empty rows are dropped.
    """
    ...


def group_forms_by_resource(form_paths: list[Path]) -> dict[str, list[Path]]:
    """Group forms by the resource they should map to."""
    grouped_forms: dict[str, list[Path]] = defaultdict(list)
    for form_path in form_paths:
        form_name = form_path.stem
        # TODO: refine this
        if form_name.startswith("vas"):
            resource_name = "vas"
        elif form_name.startswith("sefnc"):
            resource_name = "sefnc"
            ...
        else:
            resource_name = "other"
        grouped_forms[resource_name].append(form_path)

    return grouped_forms


def stage_other_resources(
    staging_dir: Path,
    form_paths: list[Path],
) -> None:
    """Stage forms that need no special processing."""
    ...
