from collections import defaultdict
from dataclasses import dataclass
from operator import itemgetter
from pathlib import Path

import polars as pl
import seedcase_soil as so


@dataclass
class Form:
    """Class to hold the name and data of a form."""

    name: str
    data: pl.DataFrame


REDCAP_ID_COLS = [
    "record_id_s",
    "redcap_event_name",
    "redcap_repeat_instrument",
    "redcap_repeat_instance",
]


def get_form_field_mapping(
    field_metadata: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Get a mapping from form name to a list of field names in that form."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for field in field_metadata:
        mapping[field["form_name"]].append(field["field_name"])

    return mapping


def get_form_event_mapping(
    event_metadata: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Get a mapping from form names to event names where the form is filled in."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for item in event_metadata:
        mapping[item["form"]].append(item["unique_event_name"])

    return mapping


def get_repeating_forms(repeating_forms: list[dict[str, str]]) -> set[str]:
    """Get the set of repeating form names."""
    return set(so.fmap(repeating_forms, itemgetter("form_name")))


def split_forms(
    raw_data_path: Path,
    form_to_fields: dict[str, list[str]],
    form_to_events: dict[str, list[str]],
    repeating_form_names: set[str],
) -> list[Form]:
    """Split data into one Parquet file per form."""
    raw_lf = pl.scan_csv(raw_data_path, infer_schema=False)
    raw_lf = _add_missing_columns(raw_lf, form_to_fields)

    return _split_data_by_form(
        raw_lf, form_to_fields, form_to_events, repeating_form_names
    )


def write_form(form: Form, forms_dir: Path, timestamp: str) -> None:
    """Write the dataframe."""
    file_path = forms_dir / timestamp / f"{form.name}.parquet"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    form.data.write_parquet(file_path)


def _add_missing_columns(
    lf: pl.LazyFrame, form_to_fields: dict[str, list[str]]
) -> pl.LazyFrame:
    """Add any missing metadata fields as columns in the dataframe."""
    metadata_fields = so.flat_fmap(form_to_fields.values(), lambda fields: fields)
    data_fields = set(lf.collect_schema().names())
    missing_fields = so.keep(metadata_fields, lambda field: field not in data_fields)
    return lf.with_columns(so.fmap(missing_fields, pl.lit(None).alias))


def _split_data_by_form(
    raw_lf: pl.LazyFrame,
    form_to_fields: dict[str, list[str]],
    form_to_events: dict[str, list[str]],
    repeating_form_names: set[str],
) -> list[Form]:
    """Split the raw data into one dataframe per form."""
    forms = so.fmap(
        form_to_fields.items(),
        lambda form_entry: _create_df_for_form(
            form_entry, raw_lf, form_to_events, repeating_form_names
        ),
    )
    return so.keep(forms, lambda form: not form.data.is_empty())


def _create_df_for_form(
    form_entry: tuple[str, list[str]],
    raw_lf: pl.LazyFrame,
    form_to_events: dict[str, list[str]],
    repeating_form_names: set[str],
) -> Form:
    form_name, field_names = form_entry
    events = form_to_events.get(form_name, [])
    is_repeating = form_name in repeating_form_names
    content_fields = so.keep(field_names, lambda field: field not in REDCAP_ID_COLS)

    columns = [
        pl.col("record_id_s").alias("participant_id"),
        pl.col("redcap_event_name").alias("event_id"),
        *so.fmap(content_fields, pl.col),
        # TODO: handle different centers
        pl.lit("Copenhagen").alias("center"),
    ]

    if is_repeating:
        # Submissions for the same participant at the same event are told apart by
        # `redcap_repeat_instance`.
        columns.insert(
            2, pl.col("redcap_repeat_instance").cast(pl.String).alias("submission_id")
        )

    filters = [
        # Keep only rows coming from events where the form was filled in
        pl.col("redcap_event_name").is_in(events),
        # Keep only non-empty rows
        pl.any_horizontal(
            so.fmap(content_fields, lambda field: pl.col(field).is_not_null())
        ),
    ]

    return Form(name=form_name, data=raw_lf.filter(filters).select(columns).collect())
