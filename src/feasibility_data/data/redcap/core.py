from dataclasses import dataclass
from pathlib import Path

import polars as pl
import seedcase_soil as so

from feasibility_data import metadata


@dataclass(frozen=True)
class Form:
    """Class to hold the metadata and data of a form."""

    form_metadata: metadata.redcap.core.FormMetadata
    data: pl.DataFrame


REDCAP_ID_COLS = [
    "record_id_s",
    "redcap_event_name",
    "redcap_repeat_instrument",
    "redcap_repeat_instance",
]


def read_raw(
    raw_data_path: Path, forms_metadata: list[metadata.redcap.core.FormMetadata]
) -> pl.LazyFrame:
    """Read the raw data into a LazyFrame with missing columns added.

    A LazyFrame lets Polars build a query plan and optimise it before executing, rather
    than materialising intermediate results at each step. With a separate query for each
    form and thousands of columns in the raw data, this meaningfully reduces computation
    time compared to eager evaluation.
    """
    raw_lf = pl.scan_csv(raw_data_path, infer_schema=False)
    return _with_missing_columns(raw_lf, forms_metadata)


def split_forms(
    raw_lf: pl.LazyFrame,
    forms_metadata: list[metadata.redcap.core.FormMetadata],
) -> list[Form]:
    """Split the raw data into one dataframe per form."""
    lazy_dfs = so.pairwise_fmap(forms_metadata, [raw_lf], _create_df_for_form)
    dfs = pl.collect_all(lazy_dfs)
    forms = so.pairwise_fmap(forms_metadata, dfs, Form)
    return so.keep(forms, lambda form: not form.data.is_empty())


def write_form(form: Form, forms_dir: Path, raw_data_path: Path) -> None:
    """Write the dataframe."""
    timestamp = raw_data_path.name.removesuffix(".csv.gz")
    file_path = forms_dir / timestamp / f"{form.form_metadata.name}.parquet"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    form.data.write_parquet(file_path)


def _with_missing_columns(
    lf: pl.LazyFrame, forms_metadata: list[metadata.redcap.core.FormMetadata]
) -> pl.LazyFrame:
    """Add any missing metadata fields as columns in the dataframe."""
    metadata_fields = so.flat_fmap(forms_metadata, lambda form: form.fields)
    data_fields = set(lf.collect_schema().names())
    missing_fields = so.keep(metadata_fields, lambda field: field not in data_fields)
    return lf.with_columns(so.fmap(missing_fields, pl.lit(None).alias))


def _create_df_for_form(
    form_metadata: metadata.redcap.core.FormMetadata,
    raw_lf: pl.LazyFrame,
) -> pl.LazyFrame:
    content_fields = so.keep(
        form_metadata.fields, lambda field: field not in REDCAP_ID_COLS
    )

    columns = [
        pl.col("record_id_s").alias("participant_id"),
        pl.col("redcap_event_name").alias("event_id"),
        *so.fmap(content_fields, pl.col),
        # TODO: handle different centers
        pl.lit("Copenhagen").alias("center"),
    ]

    if form_metadata.repeats:
        # Submissions for the same participant at the same event are told apart by
        # `redcap_repeat_instance`.
        columns.insert(
            2, pl.col("redcap_repeat_instance").cast(pl.String).alias("submission_id")
        )

    filters = [
        # Keep only rows coming from events where the form was filled in
        pl.col("redcap_event_name").is_in(form_metadata.events),
        # Keep only non-empty rows
        pl.any_horizontal(
            so.fmap(content_fields, lambda field: pl.col(field).is_not_null())
        ),
    ]

    return raw_lf.filter(filters).select(columns)
