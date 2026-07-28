import os
from datetime import UTC, datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from feasibility_data.common.redcap import APIConfig

load_dotenv()


def download() -> requests.Response:
    """Download the myfood24 data."""
    api = APIConfig(
        # Key couldn't be named "MYFOOD24" bc the entropy became too high and
        # and was flagged by gitleaks as a secret.
        env_key="MYFOOD_API_KEY",
        url="https://myfood24.org/api/projects/23816/extract",
    )
    headers = {
        "Authorization": f"Api-Key {os.environ.get(api.env_key)}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(api.url, headers=headers, stream=True, timeout=60)
    response.raise_for_status()

    return response


def write(raw_data_dir: Path, response: requests.Response) -> None:
    """Write the myfood24 data extract zip to the `raw/myfood24/` directory."""
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    data_path = raw_data_dir / f"{timestamp}.zip"
    raw_data_dir.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
