import gzip
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import requests

from feasibility_data.common.datetime import get_current_datetime


def download() -> requests.Response:
    """Download the myfood24 data."""
    headers = {
        "Authorization": f"Api-Key {os.environ.get('MYFOOD_API_KEY')}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(
        "https://myfood24.org/api/projects/23816/extract",
        headers=headers,
        stream=True,
        timeout=60,
    )
    response.raise_for_status()

    return response


def write(response: requests.Response, output_dir: Path) -> None:
    """Write the myfood24 data extract `.csv.gz` files to the raw directory."""
    # Create raw data dir. Strictly not necessary because pytask creates the dir, but
    # useful if we ever need to run this outside the pytask pipeline.
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write zip to temporary file.
    with tempfile.NamedTemporaryFile(suffix=".zip") as temp_file:
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        # Ensure data is written to disk.
        temp_file.flush()

        # Extract each CSV from the archive and recompress it as `.csv.gz`.
        with zipfile.ZipFile(temp_file.name) as zip_file:
            current_datetime = get_current_datetime()

            for file in zip_file.infolist():
                output_path = (
                    output_dir / f"{Path(file.filename).stem}-{current_datetime}.csv.gz"
                )

                with (
                    zip_file.open(file) as source_file,
                    gzip.open(output_path, "wb") as target_file,
                ):
                    shutil.copyfileobj(source_file, target_file)
