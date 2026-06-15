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

# TODO: Get from file
FORM_EVENTS = {
    "stamdata": ["stamdata_arm_1"],
    "adverse_events": ["stamdata_arm_1"],
    "bookinger": ["stamdata_arm_1"],
    "randomisering": ["randomisering_arm_1"],
    "prscreening_telefoninterview_frste_kontakt": ["prscreening_arm_1"],
    "fr_besgsdag_1_screening": ["besg_1__screening_arm_1"],
    "besg_1_screening": ["besg_1__screening_arm_1"],
    "bedq": ["besg_1__screening_arm_1"],
    "foer_besoegsdag_2": ["besg_2_arm_1"],
    "besoegsdag_2": ["besg_2_arm_1"],
    "vas_minus10": [
        "besg_2_arm_1",
        "besg_3_arm_1",
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_8_arm_1",
        "besg_10_arm_1",
    ],
    "vas_30min": [
        "besg_2_arm_1",
        "besg_3_arm_1",
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_8_arm_1",
        "besg_10_arm_1",
    ],
    "vas_60min": [
        "besg_2_arm_1",
        "besg_3_arm_1",
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_8_arm_1",
        "besg_10_arm_1",
    ],
    "vas_90_min": [
        "besg_2_arm_1",
        "besg_3_arm_1",
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_8_arm_1",
        "besg_10_arm_1",
    ],
    "vas_120_min": [
        "besg_2_arm_1",
        "besg_3_arm_1",
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_8_arm_1",
        "besg_10_arm_1",
    ],
    "vas_180_min": [
        "besg_2_arm_1",
        "besg_3_arm_1",
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_8_arm_1",
        "besg_10_arm_1",
    ],
    "vas_240_min": [
        "besg_2_arm_1",
        "besg_3_arm_1",
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_8_arm_1",
        "besg_10_arm_1",
    ],
    "foer_besoegsdag_3": ["besg_3_arm_1"],
    "besoegsdag_3": ["besg_3_arm_1"],
    "foer_besoegsdag_4": ["besg_4_arm_1"],
    "besoegsdag_4": ["besg_4_arm_1"],
    "sociodemografiske_karakteristika": ["besg_4_arm_1"],
    "diabetes_status": ["besg_4_arm_1", "besg_10_arm_1"],
    "pittsburgh_sleep_quality_index_psqi": [
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_10_arm_1",
    ],
    "physical_and_mental_health_sf12": [
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_10_arm_1",
    ],
    "european_quality_of_life_5_dimensions_eq5d5l": [
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_10_arm_1",
    ],
    "tobacco_and_nicotine_use": ["besg_4_arm_1", "besg_6_arm_1", "besg_10_arm_1"],
    "sefnc_baseline_v4": ["besg_4_arm_1"],
    "the_three_item_loneliness_scale_tils": [
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_10_arm_1",
    ],
    "item_bodily_distress_syndrome_checklist": [
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_10_arm_1",
    ],
    "yale_food_addiction_scale_yfas": ["besg_4_arm_1", "besg_6_arm_1", "besg_10_arm_1"],
    "social_support_for_eating_habits": [
        "besg_4_arm_1",
        "besg_6_arm_1",
        "besg_10_arm_1",
    ],
    "diabetes_distress_paid5_scale": ["besg_4_arm_1", "besg_6_arm_1", "besg_10_arm_1"],
    "fr_besgsdag_5": ["besg_5_arm_1"],
    "besgsdag_5": ["besg_5_arm_1"],
    "fr_besgsdag_6": ["besg_6_arm_1"],
    "besgsdag_6": ["besg_6_arm_1"],
    "sefnc_week12_v6": ["besg_6_arm_1"],
    "fr_besgsdag_7": ["besg_7_arm_1"],
    "besgsdag_7": ["besg_7_arm_1"],
    "fr_besgsdag_8": ["besg_8_arm_1"],
    "besgsdag_8": ["besg_8_arm_1"],
    "hba1c_uge_30": ["hba1c_30_uger_arm_1"],
    "hba1c_uge_42": ["hba1c_42_uger_arm_1"],
    "fr_besgsdag_9": ["besg_9_arm_1"],
    "besoegsdag_9": ["besg_9_arm_1"],
    "fr_besgsdag_5_9bba": ["besg_10_arm_1"],
    "besgsdag_10_5f76": ["besg_10_arm_1"],
    "sociodemografiske_karakteristika_short": ["besg_10_arm_1"],
    "selfefficacy_for_nutrition_change_sefnc_week_52": ["besg_10_arm_1"],
    "gruppemde_uge_1": ["fase_1_arm_1"],
    "gruppemde_uge_3": ["fase_1_arm_1"],
    "gruppemde_uge_5": ["fase_1_arm_1"],
    "gruppemde_uge_7": ["fase_1_arm_1"],
    "gruppemde_uge_9": ["fase_1_arm_1"],
    "gruppemde_uge_11": ["fase_1_arm_1"],
    "fase_1_ditetiske_afvigelser": ["fase_1_arm_1"],
    "gruppemde_uge_13": ["fase_2_arm_1"],
    "gruppemde_uge_15": ["fase_2_arm_1"],
    "gruppemde_uge_17": ["fase_2_arm_1"],
    "gruppemde_uge_18": ["fase_2_arm_1"],
    "fase_2_ditetiske_afvigelser": ["fase_2_arm_1"],
    "individuel_ditistsamtale_1": ["fase_3_arm_1"],
    "individuel_ditistsamtale_2": ["fase_3_arm_1"],
    "individuel_ditistsamtale_3": ["fase_3_arm_1"],
    "individuel_ditistsamtale_4": ["fase_3_arm_1"],
    "fase_3_ditetiske_afvigelser": ["fase_3_arm_1"],
    "trningsafvigelser": ["fase_3_arm_1"],
    "ekstra_kontakt": ["ekstra_kontaktsttt_arm_1"],
    "medicine_changes": ["medicinndringer_arm_1"],
    "hba1c_follow_up": ["hba1c_ekstra_mling_arm_1"],
}


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
