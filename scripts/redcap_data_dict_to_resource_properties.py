import json
import re
from itertools import chain, groupby
from operator import itemgetter
from pathlib import Path
from typing import Callable, Iterable, Optional, TypeVar, cast

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


def load_data_dict_from_file() -> list[dict[str, str]]:
    """Loads REDCap data dictionary from `scripts/data_dictionary.json`."""
    with open(Path("scripts") / "data_dictionary.json") as f:
        return json.load(f)


def redcap_data_dict_to_resource_properties(
    redcap_fields: list[dict[str, str]],
) -> list[sp.ResourceProperties]:
    """Converts REDCap data dictionary to Data Package resources."""
    sorted_by_form = sorted(redcap_fields, key=lambda field: field["form_name"])
    grouped_by_form = groupby(sorted_by_form, key=lambda field: field["form_name"])
    return _map(
        grouped_by_form,
        lambda group: _redcap_form_to_resource(group[0], list(group[1])),
    )


def _redcap_form_to_resource(
    form_name: str, fields: list[dict[str, str]]
) -> sp.ResourceProperties:
    visit_field = sp.FieldProperties(
        name="visit",
        title="The unique name of the visit.",
        type="string",
        description=(
            "The unique name identifying the visit. A visit "
            "corresponds to a REDCap event when the the form was filled in."
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
            description=_get_description(field),
            categories=_get_categories(field),
            constraints=sp.ConstraintsProperties(
                required=_get_required(field),
                enum=_get_categories(field),
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
            primary_key=["visit"],
            fields=[visit_field] + form_fields + checkbox_fields,
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


def _get_type(redcap_field: dict[str, str]) -> sp.properties.FieldType:
    match redcap_field["field_type"]:
        case "text" | "calc" | "radio" | "notes" | "file":
            return "string"
        case "slider":
            return "number"
        case _:
            raise NotImplementedError(_get_error_message(redcap_field, "field_type"))
