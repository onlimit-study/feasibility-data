import re
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from typing import cast

import polars as pl
import seedcase_soil as so

VAS_TIME_FIELD_PATTERN = re.compile(
    r"^vas_(?P<field_name>.+?)(_fasted)?_(?P<time>minus10|30|60|90|120|180|240)min$"
)


def load_raw_data() -> pl.DataFrame:
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


def _select_with_base_cols(
    raw_df: pl.DataFrame, resource_name: str, cols: list[str]
) -> pl.DataFrame:
    """Selects columns and adds base columns common to all dataframes."""
    return (
        raw_df.select(["redcap_event_name"] + cols)
        .rename({"redcap_event_name": "event"})
        .with_columns(
            pl.lit("Copenhagen").alias("center"),
            pl.lit(resource_name).alias("resource_name"),
        )
    )


def raw_to_staged(raw_df: pl.DataFrame) -> list[pl.DataFrame]:
    """Transforms the raw data into staged dataframes."""
    resources = _get_fields_by_resource()

    # Resources with special handling
    resources.pop("vas", None)
    dfs = [_create_vas_df(raw_df)]

    # Resources without special handling
    return dfs + so.pairwise_fmap(
        list(resources.items()), [raw_df], _create_df_for_resource
    )


def _create_df_for_resource(
    resource_entry: tuple[str, list[str]], raw_df: pl.DataFrame
) -> pl.DataFrame:
    """Creates a dataframe for a resource."""
    resource_name, field_names = resource_entry

    # Remove fields not in the raw data
    field_names.remove("event")
    field_names.remove("center")

    return _select_with_base_cols(raw_df, resource_name, field_names)


def _create_vas_df(raw_df: pl.DataFrame) -> pl.DataFrame:
    """Creates a dataframe for the VAS resource."""
    vas_cols = so.keep(
        raw_df.columns,
        lambda column: VAS_TIME_FIELD_PATTERN.match(column) is not None,
    )

    cols_grouped_by_time: dict[int, list[str]] = {}
    for col in vas_cols:
        match = cast(re.Match[str], VAS_TIME_FIELD_PATTERN.match(col))

        time = match.group("time")
        if time == "minus10":
            time = "-10"

        cols_grouped_by_time.setdefault(int(time), []).append(col)

    vas_dfs = so.pairwise_fmap(
        list(cols_grouped_by_time.items()), [raw_df], _create_df_for_time_group
    )
    return pl.concat(vas_dfs, how="vertical")


def _create_df_for_time_group(
    time_group: tuple[int, list[str]], raw_df: pl.DataFrame
) -> pl.DataFrame:
    """Creates a dataframe for a group of VAS columns with the same time."""
    time, cols = time_group

    renamed_cols = {
        col: cast(re.Match[str], VAS_TIME_FIELD_PATTERN.match(col)).group("field_name")
        for col in cols
    }

    return (
        _select_with_base_cols(raw_df, "vas", cols)
        .rename(renamed_cols)
        .with_columns(pl.lit(time).alias("minutes_from_meal"))
    )


def write_staged_df(df: pl.DataFrame) -> None:
    """Writes the dataframe to `staging/redcap/<resource-name>/<timestamp>.parquet`."""
    resource_name = df["resource_name"][0]
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    file_path = Path("staging") / "redcap" / resource_name / f"{timestamp}.parquet"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df.drop("resource_name").write_parquet(file_path)
    so.pretty_print(f"Wrote staged data to '{file_path}'.")


if __name__ == "__main__":
    raw = load_raw_data()
    for df in raw_to_staged(raw):
        write_staged_df(df)
