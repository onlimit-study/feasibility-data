import json
import re
from itertools import chain, groupby
from operator import itemgetter
from pathlib import Path
from typing import Callable, Iterable, Literal, Optional, TypeVar, Union, cast

import seedcase_sprout as sp

In = TypeVar("In")
Out = TypeVar("Out")


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
    sorted_by_form = sorted(redcap_fields, key=lambda field: field["form_name"])
    grouped_by_form = groupby(sorted_by_form, key=lambda field: field["form_name"])
    return _map(
        grouped_by_form,
        lambda group: _form_to_resource(group[0], list(group[1])),
    )


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

    return sp.ResourceProperties(
        name=form_name,
        # TODO: fill in title and description
        title=form_name,
        description=form_name,
        schema=sp.TableSchemaProperties(
            primary_key=["event"],
            fields=[event_field, center_field] + form_fields + checkbox_fields,
        ),
    )


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
