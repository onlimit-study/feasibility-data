import gzip
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv

from feasibility_data.common.datetime import get_current_datetime
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
    """Write the myfood24 data extract `.csv.gz` files to the raw directory."""
    # Write zip to temporary file.
    with tempfile.NamedTemporaryFile(suffix=".zip") as temp_file:
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        # Ensure data is written to disk.
        temp_file.flush()

        # Extract each CSV from the archive and recompress it as `.csv.gz`.
        with zipfile.ZipFile(temp_file.name) as zip_file:
            for file in zip_file.infolist():
                output_path = (
                    raw_data_dir
                    / f"{Path(file.filename).stem}-{get_current_datetime()}.csv.gz"
                )

                with (
                    zip_file.open(file) as source_file,
                    gzip.open(output_path, "wb") as target_file,
                ):
                    shutil.copyfileobj(source_file, target_file)
