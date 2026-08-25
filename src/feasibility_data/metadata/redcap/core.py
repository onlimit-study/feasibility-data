import re
from dataclasses import dataclass
from typing import Any, cast

import polars as pl
import seedcase_soil as so


@dataclass(frozen=True)
class FormMetadata:
    """Class to hold the metadata of a form."""

    name: str
    fields: list[str]
    events: list[str]
    repeats: bool


def create_form_metadata(
    field_df: pl.DataFrame,
    event_df: pl.DataFrame,
    repeating_forms_df: pl.DataFrame,
) -> list[dict[str, Any]]:
    """Create the metadata for each form."""
    field_df = field_df.group_by("form_name", maintain_order=True).agg(
        pl.col("field_name").alias("fields")
    )
    event_df = (
        event_df.group_by("form", maintain_order=True)
        .agg(pl.col("unique_event_name").alias("events"))
        .rename({"form": "form_name"})
    )
    repeating_form_names = repeating_forms_df.get_column("form_name").unique()
    form_df = field_df.join(event_df, on="form_name", how="left").with_columns(
        pl.col("form_name").is_in(repeating_form_names).alias("repeats"),
        pl.col("events").fill_null([]),
    )
    return form_df.select(
        pl.col("form_name").alias("name"),
        pl.col("fields"),
        pl.col("events"),
        pl.col("repeats"),
    ).to_dicts()


def expand_checkbox_fields(
    field_metadata: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Expand checkbox fields in the field metadata."""
    checkbox_fields = so.keep(
        field_metadata, lambda field: field["field_type"] == "checkbox"
    )
    non_checkbox_fields = so.keep(
        field_metadata, lambda field: field["field_type"] != "checkbox"
    )
    expanded_fields = so.flat_fmap(checkbox_fields, _expand_checkbox_field)

    return non_checkbox_fields + expanded_fields


def _expand_checkbox_field(checkbox_field: dict[str, str]) -> list[dict[str, str]]:
    return so.fmap(
        _get_choices(checkbox_field),
        lambda choice: (
            checkbox_field
            | {
                "field_name": f"{checkbox_field['field_name']}___{choice[0]}",
                "field_label": choice[1],
            }
        ),
    )


def _get_choices(field: dict[str, str]) -> list[tuple[str, str]]:
    """Parses the choices into the choice number and choice value.

    E.g.:
        Input: "1, first choice|2, second choice|3, third choice"
        Output: [('1', 'first choice'), ('2', 'second choice'), ('3', 'third choice')]
    """
    choices = field["select_choices_or_calculations"].split("|")
    matches = so.fmap(
        choices, lambda choice: re.match(r"^(\d+), *(.*)", choice.strip())
    )
    if not all(matches):
        raise ValueError(_get_error_message(field, "select_choices_or_calculations"))
    return so.fmap(
        cast(list[re.Match[str]], matches),
        lambda match: (match.group(1), match.group(2)),
    )


def _get_error_message(field: dict[str, str], key: str) -> str:
    return (
        f"Unexpected value {field[key]!r} for `{key}` in field {field['field_name']!r} "
        f"in form {field['form_name']!r}."
    )
