import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

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
    Test = APIConfig(env_key="TEST_API_KEY", url="https://redcap.au.dk/api/")


def get_from_redcap(
    data: dict[str, str],
    center: Center = Center.Copenhagen,
) -> requests.Response:
    """Send a request to the REDCap API."""
    token = os.environ.get(center.value.env_key)
    if not token:
        raise RuntimeError(f"{center.value.env_key} environment variable is not set.")

    data["token"] = token

    response = requests.post(center.value.url, data=data, timeout=60)
    response.raise_for_status()

    return response


def get_json_from_redcap(
    content: str,
    center: Center = Center.Copenhagen,
) -> Any:
    """Send a request to the REDCap API and return the JSON response."""
    data = {
        "content": content,
        "format": "json",
        "returnFormat": "json",
    }
    response = get_from_redcap(data, center)
    return response.json()
