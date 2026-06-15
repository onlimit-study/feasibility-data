import json
from collections import defaultdict
from datetime import datetime
from operator import itemgetter
from pathlib import Path

import polars as pl
import seedcase_soil as so

# TODO: Get from file when PK PR merged
REPEATING_RESOURCES = {
    "fase_2_ditetiske_afvigelser",
    "medicine_changes",
    "trningsafvigelser",
    "fase_1_ditetiske_afvigelser",
    "hba1c_follow_up",
    "ekstra_kontakt",
    "adverse_events",
    "fase_3_ditetiske_afvigelser",
}


def _read_form_event_mapping() -> dict[str, list[str]]:
    """Creates a mapping from form names to event names where the form is filled in."""
    with open(Path("scripts") / "form_event.json") as f:
        contents = json.load(f)

    mapping: dict[str, list[str]] = defaultdict(list)
    for item in contents:
        mapping[item["form"]].append(item["unique_event_name"])

    return mapping


FORM_EVENTS = _read_form_event_mapping()


def load_latest_raw_redcap_data() -> pl.DataFrame:
    """Loads the latest raw data from `raw/redcap/<timestamp>.csv.gz`."""
    file_path = Path("raw") / "redcap"
    files = list(file_path.glob("*.csv.gz"))
    if not files:
        raise FileNotFoundError(
            f"No raw data files found in '{file_path}'. "
            "Have you run `just download-data`?"
        )

    latest_file = max(files, key=lambda file: file.name)
    so.pretty_print(f"Loading data from '{latest_file}'.")
    return pl.read_csv(latest_file)


def raw_to_staged(raw_df: pl.DataFrame) -> list[pl.DataFrame]:
    """Transforms the raw data into staged dataframes."""
    resources = _get_fields_by_resource()

    # Resources with special handling
    # TODO: Create these resources separately
    resources.pop("vas", None)
    resources.pop("sefnc", None)

    # Resources without special handling
    dfs = so.pairwise_fmap(list(resources.items()), [raw_df], _create_df_for_resource)
    return so.keep(dfs, lambda df: not df.is_empty())


def write_staged_df(df: pl.DataFrame) -> None:
    """Writes the dataframe to `staging/redcap/<resource-name>/<timestamp>.parquet`."""
    resource_name = df["resource_name"][0]
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    file_path = Path("staging") / "redcap" / resource_name / f"{timestamp}.parquet"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df.drop("resource_name").write_parquet(file_path)
    so.pretty_print(f"Wrote staged data to '{file_path}'.")


def _get_fields_by_resource() -> dict[str, list[str]]:
    """Gets a mapping from resource names to a list of field names in that resource."""
    properties = so.read_properties(so.parse_source("datapackage.json"))
    return dict(
        so.fmap(
            properties["resources"],
            lambda resource: (
                resource["name"],
                so.fmap(resource["schema"]["fields"], itemgetter("name")),
            ),
        )
    )


def _create_df_for_resource(
    resource_entry: tuple[str, list[str]],
    raw_df: pl.DataFrame,
) -> pl.DataFrame:
    resource_name, field_names = resource_entry

    content_fields = so.keep(
        field_names,
        lambda field: (
            field
            not in [
                # Will be added everywhere, not just in stamdata
                "record_id_s",
                # Will be renamed from columns in raw data
                "participant_id",
                "event_id",
                "submission_id",
                # Not in raw data
                "center",
            ]
        ),
    )
    events = FORM_EVENTS[resource_name]

    filters = [
        # Keep only rows for events where the resource was filled in
        pl.col("redcap_event_name").is_in(events),
        # Keep only non-empty rows
        pl.any_horizontal(
            so.fmap(content_fields, lambda field: pl.col(field).is_not_null())
        ),
    ]

    is_repeating = resource_name in REPEATING_RESOURCES
    if is_repeating:
        # Repeating resources are listed in separate rows for each submission,
        # not in the same row as data for other resources for the same event.
        # Keep only rows for the resource.
        filters.append(pl.col("redcap_repeat_instrument") == resource_name)

    columns = [
        pl.col("record_id_s").alias("participant_id"),
        pl.col("redcap_event_name").alias("event_id"),
        *so.fmap(content_fields, lambda field: pl.col(field)),
        pl.lit("Copenhagen").alias("center"),
        # Only used for creating the Parquet files.
        pl.lit(resource_name).alias("resource_name"),
    ]

    if is_repeating:
        # Different submissions for the same repeating resource are told apart by
        # `redcap_repeat_instance`.
        columns.insert(
            2, pl.col("redcap_repeat_instance").cast(pl.String).alias("submission_id")
        )

    return raw_df.filter(filters).select(columns)


if __name__ == "__main__":
    raw = load_latest_raw_redcap_data()
    for df in raw_to_staged(raw):
        write_staged_df(df)
