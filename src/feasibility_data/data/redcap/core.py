from collections import defaultdict
from operator import itemgetter
from pathlib import Path

import polars as pl
import seedcase_soil as so


def split_forms(
    forms_dir: Path,
    raw_data_path: Path,
    field_metadata: list[dict[str, str]],
    event_metadata: list[dict[str, str]],
    repeating_forms: list[dict[str, str]],
) -> None:
    """Split data into one Parquet file per form."""
    data = pl.read_csv(raw_data_path, infer_schema=False)
    timestamp = raw_data_path.name.removesuffix(".csv.gz")

    form_to_fields = _get_form_field_mapping(field_metadata)
    form_to_events = _get_form_event_mapping(event_metadata)
    repeating_form_names = _get_repeating_forms(repeating_forms)

    for df in _split_data_by_form(
        data, form_to_fields, form_to_events, repeating_form_names
    ):
        _write_df(df, forms_dir, timestamp)


def _split_data_by_form(
    raw_df: pl.DataFrame,
    form_to_fields: dict[str, list[str]],
    form_to_events: dict[str, list[str]],
    repeating_form_names: set[str],
) -> list[pl.DataFrame]:
    """Split the raw data into one dataframe per form."""
    dfs = so.fmap(
        form_to_fields.items(),
        lambda form_entry: _create_df_for_form(
            form_entry, raw_df, form_to_events, repeating_form_names
        ),
    )
    return so.keep(dfs, lambda df: not df.is_empty())


REDCAP_ID_COLS = [
    "record_id_s",
    "redcap_event_name",
    "redcap_repeat_instrument",
    "redcap_repeat_instance",
]


def _create_df_for_form(
    form_entry: tuple[str, list[str]],
    raw_df: pl.DataFrame,
    form_to_events: dict[str, list[str]],
    repeating_form_names: set[str],
) -> pl.DataFrame:
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
        # Only used for creating the Parquet files.
        pl.lit(form_name).alias("form_name"),
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

    return raw_df.filter(filters).select(columns)


def _get_form_field_mapping(
    field_metadata: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Get a mapping from form name to a list of field names in that form."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for field in field_metadata:
        mapping[field["form_name"]].append(field["field_name"])

    return mapping


def _get_form_event_mapping(
    event_metadata: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Get a mapping from form names to event names where the form is filled in."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for item in event_metadata:
        mapping[item["form"]].append(item["unique_event_name"])

    return mapping


def _get_repeating_forms(repeating_forms: list[dict[str, str]]) -> set[str]:
    """Get the set of repeating form names."""
    return set(so.fmap(repeating_forms, itemgetter("form_name")))


def _write_df(df: pl.DataFrame, forms_dir: Path, timestamp: str) -> None:
    """Write the dataframe."""
    form_name = df["form_name"][0]
    file_path = forms_dir / timestamp / f"{form_name}.parquet"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df.drop("form_name").write_parquet(file_path)
