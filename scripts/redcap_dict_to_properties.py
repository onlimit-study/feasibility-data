import json
import re
from functools import reduce
from itertools import chain, groupby
from operator import itemgetter
from pathlib import Path
from typing import Callable, Iterable, Literal, Optional, TypeVar, Union, cast

import seedcase_sprout as sp

In = TypeVar("In")
Out = TypeVar("Out")
VAS_TIMEPOINTS = [-10, 30, 60, 90, 120, 180, 240]
VAS_TIME_FORM_PATTERN = re.compile(r"^vas_(minus10|(30|60|90|120|180|240)_?min)$")
VAS_TIME_FIELD_PATTERN = re.compile(r"(_fasted)?_(minus10|30|60|90|120|180|240)min$")
SEFNC_WEEKS = [0, 12, 52]
SEFNC_FORM_WEEKS = {
    "sefnc_baseline_v4": 0,
    "sefnc_week12_v6": 12,
    "selfefficacy_for_nutrition_change_sefnc_week_52": 52,
}
SEFNC_WEEK_FIELD_PATTERN = re.compile(r"_v(6|10)$")
FOER_BESOEGSDAG_VISITS = [2, 3, 4]
FOER_BESOEGSDAG_FORM_VISITS = {
    "foer_besoegsdag_2": 2,
    "foer_besoegsdag_3": 3,
    "foer_besoegsdag_4": 4,
}
FOER_BESOEGSDAG_VISIT_FIELD_PATTERN = re.compile(r"_wfv(2|3|4)$")


def _map(x: Iterable[In], fn: Callable[[In], Out]) -> list[Out]:
    return list(map(fn, x))


def _filter(x: Iterable[In], fn: Callable[[In], bool]) -> list[In]:
    return list(filter(fn, x))


def _flat_map(items: Iterable[In], fn: Callable[[In], Iterable[Out]]) -> list[Out]:
    """Maps and flattens the items by one level."""
    return list(chain.from_iterable(map(fn, items)))


def read_dictionary() -> list[dict[str, str]]:
    """Loads REDCap data dictionary from `scripts/data_dictionary.json`."""
    with open(Path("scripts") / "data_dictionary.json") as f:
        return json.load(f)


def dictionary_to_properties(
    redcap_fields: list[dict[str, str]],
) -> list[sp.ResourceProperties]:
    """Converts REDCap data dictionary to Data Package resources."""
    redcap_fields = _join_vas_time_resources(redcap_fields)
    redcap_fields = _join_sefnc_week_resources(redcap_fields)
    redcap_fields = _join_foer_besoegsdag_visit_resources(redcap_fields)
    sorted_by_form = sorted(redcap_fields, key=lambda field: field["form_name"])
    grouped_by_form = groupby(sorted_by_form, key=lambda field: field["form_name"])
    return _map(
        grouped_by_form,
        lambda group: _form_to_resource(group[0], list(group[1])),
    )


def _join_vas_time_resources(
    redcap_fields: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Combines REDCap VAS timepoint forms into one resource schema."""
    return _deduplicate_vas_fields(
        _map(redcap_fields, _normalise_vas_time_resource_field)
    )


def _normalise_vas_time_resource_field(field: dict[str, str]) -> dict[str, str]:
    if not _is_vas_time_resource_field(field):
        return field

    return {
        **field,
        "field_name": _normalise_vas_field_name(field["field_name"]),
        "form_name": "vas",
        "field_annotation": _remove_vas_time_from_annotation(field["field_annotation"]),
    }


def _normalise_vas_field_name(field_name: str) -> str:
    return re.sub(r"^vas_", "", VAS_TIME_FIELD_PATTERN.sub("", field_name))


def _is_vas_time_resource_field(field: dict[str, str]) -> bool:
    return bool(VAS_TIME_FORM_PATTERN.match(field["form_name"]))


def _deduplicate_vas_fields(fields: list[dict[str, str]]) -> list[dict[str, str]]:
    deduplicated_fields, _ = reduce(
        _append_if_new_vas_field,
        fields,
        ([], set()),
    )
    return deduplicated_fields


def _append_if_new_vas_field(
    result: tuple[list[dict[str, str]], set[str]], field: dict[str, str]
) -> tuple[list[dict[str, str]], set[str]]:
    fields, seen_vas_fields = result
    field_name = field["field_name"]

    if field["form_name"] != "vas":
        return fields + [field], seen_vas_fields

    if field_name in seen_vas_fields:
        return result

    return (fields + [field], seen_vas_fields.union({field_name}))


def _remove_vas_time_from_annotation(annotation: str) -> str:
    return re.sub(
        r",?\s+at time\s+(minus\s+10|\d+)\s*min",
        "",
        annotation,
        flags=re.IGNORECASE,
    ).strip()


def _join_sefnc_week_resources(
    redcap_fields: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Combines SEFNC week-specific forms into one resource schema."""
    return _deduplicate_sefnc_fields(
        _map(redcap_fields, _normalise_sefnc_week_resource_field)
    )


def _normalise_sefnc_week_resource_field(field: dict[str, str]) -> dict[str, str]:
    if not _is_sefnc_week_resource_field(field):
        return field

    return {
        **field,
        "field_name": _normalise_sefnc_field_name(field["field_name"]),
        "form_name": "sefnc",
        "field_annotation": _remove_sefnc_week_from_annotation(
            field["field_annotation"]
        ),
    }


def _normalise_sefnc_field_name(field_name: str) -> str:
    return SEFNC_WEEK_FIELD_PATTERN.sub("", field_name).replace(
        "sefnc_ubusy_schedule", "sefnc_busy_schedule"
    )


def _is_sefnc_week_resource_field(field: dict[str, str]) -> bool:
    return field["form_name"] in SEFNC_FORM_WEEKS


def _deduplicate_sefnc_fields(fields: list[dict[str, str]]) -> list[dict[str, str]]:
    deduplicated_fields, _ = reduce(
        _append_if_new_sefnc_field,
        fields,
        ([], set()),
    )
    return deduplicated_fields


def _append_if_new_sefnc_field(
    result: tuple[list[dict[str, str]], set[str]], field: dict[str, str]
) -> tuple[list[dict[str, str]], set[str]]:
    fields, seen_sefnc_fields = result
    field_name = field["field_name"]

    if field["form_name"] != "sefnc":
        return fields + [field], seen_sefnc_fields

    if field_name in seen_sefnc_fields:
        return result

    return (fields + [field], seen_sefnc_fields.union({field_name}))


def _remove_sefnc_week_from_annotation(annotation: str) -> str:
    annotation = re.sub(
        r"\s+Repeated at baseline \(V4\), week 12 \(V6\) and week 52 \(V10\)\.?",
        "",
        annotation,
        flags=re.IGNORECASE,
    )

    return re.sub(
        r"\s+(Baseline|Week 12|Week 52)\s*\((V4|V6|V?10)\)\.?",
        "",
        annotation,
        flags=re.IGNORECASE,
    ).strip()


def _join_foer_besoegsdag_visit_resources(
    redcap_fields: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Combines before-visit-day workflow forms into one resource schema."""
    common_fields = _get_common_foer_besoegsdag_field_names(redcap_fields)
    return _deduplicate_foer_besoegsdag_fields(
        _map(
            redcap_fields,
            lambda field: _normalise_foer_besoegsdag_visit_resource_field(
                field, common_fields
            ),
        )
    )


def _get_common_foer_besoegsdag_field_names(
    redcap_fields: list[dict[str, str]],
) -> set[str]:
    visit_fields = _map(
        _filter(redcap_fields, _is_foer_besoegsdag_visit_resource_field),
        lambda field: (
            _normalise_foer_besoegsdag_field_name(field["field_name"]),
            FOER_BESOEGSDAG_FORM_VISITS[field["form_name"]],
        ),
    )
    field_visits = reduce(_add_foer_besoegsdag_field_visit, visit_fields, {})

    return set(
        _map(
            _filter(
                field_visits.items(),
                lambda item: item[1] == set(FOER_BESOEGSDAG_VISITS),
            ),
            itemgetter(0),
        )
    )


def _add_foer_besoegsdag_field_visit(
    field_visits: dict[str, set[int]], visit_field: tuple[str, int]
) -> dict[str, set[int]]:
    field_name, visit = visit_field
    return {
        **field_visits,
        field_name: field_visits.get(field_name, set()).union({visit}),
    }


def _normalise_foer_besoegsdag_visit_resource_field(
    field: dict[str, str], common_fields: set[str]
) -> dict[str, str]:
    if not _is_foer_besoegsdag_visit_resource_field(field):
        return field

    field_name = _normalise_foer_besoegsdag_field_name(field["field_name"])
    return {
        **field,
        "field_name": field_name,
        "form_name": "foer_besoegsdag",
        "required_field": field["required_field"]
        if field_name in common_fields
        else "",
        "field_annotation": _remove_foer_besoegsdag_visit_from_annotation(
            field["field_annotation"]
        ),
    }


def _normalise_foer_besoegsdag_field_name(field_name: str) -> str:
    return FOER_BESOEGSDAG_VISIT_FIELD_PATTERN.sub("", field_name)


def _is_foer_besoegsdag_visit_resource_field(field: dict[str, str]) -> bool:
    return field["form_name"] in FOER_BESOEGSDAG_FORM_VISITS


def _deduplicate_foer_besoegsdag_fields(
    fields: list[dict[str, str]],
) -> list[dict[str, str]]:
    deduplicated_fields, _ = reduce(
        _append_if_new_foer_besoegsdag_field,
        fields,
        ([], set()),
    )
    return deduplicated_fields


def _append_if_new_foer_besoegsdag_field(
    result: tuple[list[dict[str, str]], set[str]], field: dict[str, str]
) -> tuple[list[dict[str, str]], set[str]]:
    fields, seen_foer_besoegsdag_fields = result
    field_name = field["field_name"]

    if field["form_name"] != "foer_besoegsdag":
        return fields + [field], seen_foer_besoegsdag_fields

    if field_name in seen_foer_besoegsdag_fields:
        return result

    return (fields + [field], seen_foer_besoegsdag_fields.union({field_name}))


def _remove_foer_besoegsdag_visit_from_annotation(annotation: str) -> str:
    annotation = re.sub(r"\s+Visit\s+[234]\.$", "", annotation, flags=re.IGNORECASE)
    return re.sub(r"\s+Wfv[234]\.$", "", annotation, flags=re.IGNORECASE).strip()


def _form_to_resource(
    form_name: str, fields: list[dict[str, str]]
) -> sp.ResourceProperties:
    event_field = sp.FieldProperties(
        name="event",
        title="The unique name of the event",
        type="string",
        description=(
            "The unique name identifying the event when the form was filled in."
        ),
        constraints=sp.ConstraintsProperties(required=True),
    )
    center_field = sp.FieldProperties(
        name="center",
        title="Research center",
        type="string",
        description="The research center where the data item was recorded.",
        categories=["Copenhagen", "Aarhus", "Odense"],
        constraints=sp.ConstraintsProperties(
            required=True,
            enum=["Copenhagen", "Aarhus", "Odense"],
        ),
    )
    default_fields = [event_field, center_field]
    primary_key = ["event"]

    if form_name == "vas":
        time_field = sp.FieldProperties(
            name="minutes_from_meal",
            title="Minutes from meal",
            type="integer",
            description=(
                "The time in minutes from the meal when the specific VAS "
                "measurement was recorded. Negative values are before the meal."
            ),
            categories=VAS_TIMEPOINTS,
            constraints=sp.ConstraintsProperties(
                required=True,
                enum=VAS_TIMEPOINTS,
            ),
        )
        default_fields.append(time_field)
        primary_key.append("minutes_from_meal")

    if form_name == "sefnc":
        week_field = sp.FieldProperties(
            name="week",
            title="Week",
            type="integer",
            description="The study week when the SEFNC measurement was recorded.",
            categories=SEFNC_WEEKS,
            constraints=sp.ConstraintsProperties(
                required=True,
                enum=SEFNC_WEEKS,
            ),
        )
        default_fields.append(week_field)
        primary_key.append("week")

    if form_name == "foer_besoegsdag":
        visit_field = sp.FieldProperties(
            name="visit",
            title="Visit",
            type="integer",
            description=(
                "The study visit that the before-visit-day workflow item was "
                "recorded for."
            ),
            categories=FOER_BESOEGSDAG_VISITS,
            constraints=sp.ConstraintsProperties(
                required=True,
                enum=FOER_BESOEGSDAG_VISITS,
            ),
        )
        default_fields.append(visit_field)
        primary_key.append("visit")

    # Discard fields displayed for information only
    form_redcap_fields = _filter(
        fields, lambda field: field["field_type"] not in ["descriptive", "checkbox"]
    )
    form_fields = _map(
        form_redcap_fields,
        lambda field: sp.FieldProperties(
            name=field["field_name"],
            title=field["field_name"],
            type=_get_type(field),
            format=_get_format(field),
            description=_get_description(field),
            categories=_get_categories(field),
            constraints=sp.ConstraintsProperties(
                required=_get_required(field),
                enum=_get_categories(field),
                minimum=_get_validation_bound(field, "text_validation_min"),
                maximum=_get_validation_bound(field, "text_validation_max"),
                min_length=_get_text_length_bound(field, "text_validation_min"),
                max_length=_get_text_length_bound(field, "text_validation_max"),
            ),
        ),
    )

    checkbox_redcap_fields = _filter(
        fields, lambda field: field["field_type"] == "checkbox"
    )
    checkbox_fields = _flat_map(checkbox_redcap_fields, _expand_checkbox_field)
    resource_title = _get_resource_title(form_name)
    resource_description = _get_resource_description(form_name)

    return sp.ResourceProperties(
        name=form_name,
        title=resource_title,
        description=resource_description,
        schema=sp.TableSchemaProperties(
            primary_key=primary_key,
            fields=default_fields + form_fields + checkbox_fields,
        ),
    )


def _get_resource_title(form_name: str) -> str:
    if form_name == "vas":
        return "Visual analogue scale measurements"

    if form_name == "sefnc":
        return "Self-efficacy for nutrition change"

    if form_name == "foer_besoegsdag":
        return "Before visit day workflow"

    return form_name


def _get_resource_description(form_name: str) -> str:
    if form_name == "vas":
        return (
            "Visual analogue scale measurements recorded at multiple timepoints "
            "relative to the meal."
        )

    if form_name == "sefnc":
        return (
            "Self-efficacy for nutrition change measurements recorded across "
            "study weeks."
        )

    if form_name == "foer_besoegsdag":
        return "Workflow items completed before study visit days."

    return form_name


def _get_error_message(field: dict[str, str], key: str) -> str:
    return (
        f"Unexpected value {field[key]!r} for `{key}` in field {field['field_name']!r} "
        f"in form {field['form_name']!r}."
    )


def _get_choices(field: dict[str, str]) -> list[tuple[str, str]]:
    """Parses the choices into the choice number and choice value.

    E.g.:
        Input: "1, first choice|2, second choice|3, third choice"
        Output: [('1', 'first choice'), ('2', 'second choice'), ('3', 'third choice')]
    """
    choices = field["select_choices_or_calculations"].split("|")
    matches = _map(choices, lambda choice: re.match(r"^(\d+), *(.*)", choice.strip()))
    if not all(matches):
        raise ValueError(_get_error_message(field, "select_choices_or_calculations"))
    return _map(
        cast(list[re.Match], matches),
        lambda match: (match.group(1), match.group(2)),
    )


def _expand_checkbox_field(checkbox_field: dict[str, str]) -> list[sp.FieldProperties]:
    return _map(
        _get_choices(checkbox_field),
        lambda choice: sp.FieldProperties(
            name=f"{checkbox_field['field_name']}___{choice[0]}",
            title=choice[1],
            type="boolean",
            description=_get_description(checkbox_field),
            constraints=sp.ConstraintsProperties(
                required=_get_required(checkbox_field),
            ),
        ),
    )


def _get_required(redcap_field: dict[str, str]) -> bool:
    match redcap_field["required_field"]:
        case "y":
            return True
        case "":
            return False
        case _:
            raise NotImplementedError(
                _get_error_message(redcap_field, "required_field")
            )


def _get_description(redcap_field: dict[str, str]) -> str:
    description = redcap_field["field_annotation"]

    # Remove action tags of the form @tag or @tag(...)
    # re.DOTALL makes . match newlines as well, which can also appear inside the
    # brackets.
    description = re.sub(r"@[\w-]+(\(.*\))?", "", description, flags=re.DOTALL).strip()

    if redcap_field["field_type"] == "calc":
        description += (
            " Derived using the formula: "
            + redcap_field["select_choices_or_calculations"]
        )

    if redcap_field["field_type"] == "slider":
        description += (
            f" Question: {redcap_field['field_label']}. Slider scale labels: "
            # Given as: left label | middle label | right label
            + redcap_field["select_choices_or_calculations"]
        )

    return description.strip()


def _get_categories(redcap_field: dict[str, str]) -> Optional[list[str]]:
    if redcap_field["field_type"] != "radio":
        return None

    return _map(_get_choices(redcap_field), itemgetter(1))


def _get_format(redcap_field: dict[str, str]) -> Optional[str]:
    match redcap_field["text_validation_type_or_show_slider_number"]:
        case "email":
            return "email"
        case "time":
            return "%H:%M"
        case "date_ymd":
            return "%Y/%m/%d"
        case "date_dmy":
            return "%d/%m/%Y"
        case "datetime_dmy":
            return "%d/%m/%Y %H:%M"
        case _:
            return None


def _get_validation_bound(
    redcap_field: dict[str, str],
    field_name: Literal["text_validation_min", "text_validation_max"],
) -> Optional[Union[float, str]]:
    mask = redcap_field["text_validation_type_or_show_slider_number"]
    value = redcap_field[field_name]
    if value == "":
        return None

    match mask:
        case "number":
            return float(value)
        case (
            "number_comma_decimal"
            | "number_1dp_comma_decimal"
            | "number_2dp_comma_decimal"
        ):
            return float(value.replace(",", "."))
        case "date_ymd" | "date_dmy" | "datetime_dmy" | "time":
            return value
        case _:
            return None


def _get_text_length_bound(
    redcap_field: dict[str, str],
    field_name: Literal["text_validation_min", "text_validation_max"],
) -> Optional[int]:
    mask = redcap_field["text_validation_type_or_show_slider_number"]
    value = redcap_field[field_name]
    if value == "":
        return None

    if mask in {"", "email", "alpha_only", "dk_cpr_dash", "cpr_med_bindestreg"}:
        return int(value)

    return None


def _get_type(redcap_field: dict[str, str]) -> sp.FieldType:
    match redcap_field["field_type"]:
        case "text":
            return _get_type_from_mask(redcap_field)
        case "calc" | "radio" | "notes" | "file":
            return "string"
        case "slider":
            return "number"
        case _:
            raise NotImplementedError(_get_error_message(redcap_field, "field_type"))


def _get_type_from_mask(redcap_field: dict[str, str]) -> sp.FieldType:
    match redcap_field["text_validation_type_or_show_slider_number"]:
        case "" | "email" | "alpha_only" | "dk_cpr_dash" | "cpr_med_bindestreg":
            return "string"
        case (
            "number"
            | "number_comma_decimal"
            | "number_1dp_comma_decimal"
            | "number_2dp_comma_decimal"
        ):
            return "number"
        case "date_ymd" | "date_dmy":
            return "date"
        case "datetime_dmy":
            return "datetime"
        case "time":
            return "time"
        case _:
            raise NotImplementedError(
                _get_error_message(
                    redcap_field, "text_validation_type_or_show_slider_number"
                )
            )
