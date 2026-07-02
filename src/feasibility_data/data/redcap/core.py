from collections import defaultdict
from operator import itemgetter
from pathlib import Path

import polars as pl
import seedcase_soil as so

from feasibility_data.common.redcap.json import read_json


def split_forms(
    forms_dir: Path,
    raw_data_path: Path,
    field_metadata_path: Path,
    event_metadata_path: Path,
    repeating_forms_path: Path,
) -> None:
    """Split data into one Parquet file per form."""
    data = pl.read_csv(raw_data_path, infer_schema=False)
    timestamp = raw_data_path.name.removesuffix(".csv.gz")

    field_metadata = read_json(field_metadata_path)
    form_to_fields = _get_form_field_mapping(field_metadata)

    event_metadata = read_json(event_metadata_path)
    form_to_events = _get_form_event_mapping(event_metadata)

    repeating_forms = read_json(repeating_forms_path)
    repeating_form_names = _get_repeating_forms(repeating_forms)

    for df in _create_dfs_for_forms(
        data, form_to_fields, form_to_events, repeating_form_names
    ):
        _write_df(df, forms_dir, timestamp)


def _create_dfs_for_forms(
    raw_df: pl.DataFrame,
    form_to_fields: dict[str, list[str]],
    form_to_events: dict[str, list[str]],
    repeating_form_names: set[str],
) -> list[pl.DataFrame]:
    """Transforms the raw data into one dataframe per form."""
    dfs = []
    for form_entry in form_to_fields.items():
        dfs.append(
            _create_df_for_form(
                form_entry, raw_df, form_to_events, repeating_form_names
            )
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

    # TODO: just for testing, remove!
    content_fields = so.keep(
        content_fields,
        lambda field: (
            field
            not in [
                "home_situation_notes_v0",
                "exclusion_reason_v0",
                "excluded_note_wfv0",
                "is_randomised",
                "isnot_randomised",
                "consent_24h_reflection_date_info_v1",
                "screening_exclusion_v1",
                "hba1c_exclusion_v1",
                "screening_done_v1",
                "mysp_guidance_v1",
                "dropout_record_v1",
                "bp_information_v2",
                "information_before_long_visit_v5",
                "information_adverse_events_v6",
                "hba1c_normal_info_v6",
                "hba1c_mildly_elevated_info_v6",
                "hba1c_elevated_info_v6",
                "information_myfood24_v7",
                "information_before_long_visit_v7",
                "information_adverse_events_v8",
                "hba1c_normal_info_v8",
                "hba1c_mildly_elevated_info_v8",
                "hba1c_elevated_info_v8",
                "information_myfood24_v9",
                "information_before_long_visit_v9",
                "information_adverse_events_v10",
                "inform_project_doctor_cgm_v10",
                "hba1c_normal_info_v10",
                "hba1c_mildly_elevated_info_v10",
                "hba1c_elevated_info_v10",
                "inform_project_doctor_cgm_group_meeting_3",
                "hba1c_normal_info_week_30",
                "hba1c_mildly_elevated_info_week_30",
                "hba1c_elevated_info_week_30",
                "hba1c_normal_info_week_42",
                "hba1c_mildly_elevated_info_week_42",
                "hba1c_elevated_info_week_42",
                "hba1c_normal_info_extra",
                "hba1c_mildly_elevated_info_extra",
                "hba1c_elevated_info_extra",
                "ds_questionnaire",
                "psqi_questionnaire",
                "sf12_questionnaire",
                "eq5d_questionnaire",
                "tobac_questionnaire",
                "sefnc_questionare",
                "sefnc_questionare_v6",
                "sefnc_questionare_v10",
                "tils_questionnaire",
                "bds_questionnaire_intro",
                "yfas_questionnaire",
                "ssfeh_questionnaire_intro",
                "paid5_questionnaire",
                "bed_q_instruction",
            ]
        ),
    )

    filters = [
        # Keep only rows for events where the form was filled in
        pl.col("redcap_event_name").is_in(events),
        # Keep only non-empty rows
        pl.any_horizontal(
            so.fmap(content_fields, lambda field: pl.col(field).is_not_null())
        ),
    ]

    if is_repeating:
        # Repeating forms are listed in separate rows for each submission,
        # not in the same row as data for other forms for the same event.
        # Keep only rows for the form.
        filters.append(pl.col("redcap_repeat_instrument") == form_name)

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
        # Different submissions for the same repeating form are told apart by
        # `redcap_repeat_instance`.
        columns.insert(
            2, pl.col("redcap_repeat_instance").cast(pl.String).alias("submission_id")
        )

    return raw_df.filter(filters).select(columns)


def _get_form_field_mapping(
    field_metadata: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Gets a mapping from form name to a list of field names in that form."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for field in field_metadata:
        mapping[field["form_name"]].append(field["field_name"])

    return mapping


def _get_form_event_mapping(
    event_metadata: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Creates a mapping from form names to event names where the form is filled in."""
    mapping: dict[str, list[str]] = defaultdict(list)
    for item in event_metadata:
        mapping[item["form"]].append(item["unique_event_name"])

    return mapping


def _get_repeating_forms(repeating_forms: list[dict[str, str]]) -> set[str]:
    """Gets a set of repeating form names."""
    return set(so.fmap(repeating_forms, itemgetter("form_name")))


def _write_df(df: pl.DataFrame, forms_dir: Path, timestamp: str) -> None:
    """Writes the dataframe."""
    form_name = df["form_name"][0]
    file_path = forms_dir / timestamp / f"{form_name}.parquet"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df.drop("form_name").write_parquet(file_path)


def group_forms_by_resource(form_paths: list[Path]) -> dict[str, list[Path]]:
    """Groups forms by target resource."""
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
    for form_path in form_paths:
        resource_name = form_path.stem
        timestamp = form_path.parent.name
        resource_path = staging_dir / resource_name / f"{timestamp}.parquet"
        resource_path.parent.mkdir(parents=True, exist_ok=True)
        pl.read_parquet(form_path).write_parquet(resource_path)
