import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class APIConfig:
    """Configuration for the REDCap API."""

    env_key: str
    url: str


class Center(Enum):
    """The centers in the study."""

    # TODO: Update these once we can connect them.
    Aarhus = APIConfig(env_key="REDC_AAR_API_KEY", url="https://redcap.auh.dk/api/")
    Copenhagen = APIConfig(
        env_key="REDC_CPH_API_KEY", url="https://redcap.regionh.dk/api/"
    )
    Odense = APIConfig(env_key="REDC_ODN_API_KEY", url="https://redcap.sdu.dk/api/")


# TODO: Update path to point to pytask build folder once we have one.
def write_dictionary(
    raw_dictionary: list[dict[str, str]],
    path: Path = Path("src/feasibility_data/metadata/redcap/dictionary.json"),
) -> Path:
    """Write dictionary from REDCap.

    Args:
        raw_dictionary: The raw dictionary data from REDCap. Gotten from `request_dictionary()`.
        path: The path to write the dictionary to.

    Returns:
        The path to the new dictionary file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(raw_dictionary, f, indent=2, ensure_ascii=False)
    return path


def request_raw_dictionary(center: Center = Center.Copenhagen) -> list[dict[str, str]]:
    """Gets the data dictionary from REDCap."""
    token = os.environ.get(center.value.env_key)
    if not token:
        raise RuntimeError(f"{center.value.env_key} environment variable is not set.")

    data = {
        "token": token,
        "content": "metadata",
        "format": "json",
        "returnFormat": "json",
    }
    response = requests.post(center.value.url, data=data, timeout=30)
    response.raise_for_status()
    dictionary: list[dict[str, str]] = response.json()
    return dictionary
