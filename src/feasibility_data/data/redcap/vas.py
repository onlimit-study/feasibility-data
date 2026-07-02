from collections import defaultdict
from pathlib import Path

import polars as pl
import seedcase_soil as so


def stage_vas(
    staging_dir: Path,
    form_paths: list[Path],
) -> None:
    """Stage VAS forms as one resource."""
    grouped_by_timestamp = defaultdict(list)
    for form_path in form_paths:
        timestamp = form_path.parent.name
        grouped_by_timestamp[timestamp].append(form_path)

    for timestamp, paths in grouped_by_timestamp.items():
        vas_forms = so.fmap(paths, pl.read_parquet)
        # TODO: process VAS forms into:
        vas_resource = pl.DataFrame(vas_forms)

        resource_path = staging_dir / "vas" / f"{timestamp}.parquet"
        resource_path.parent.mkdir(parents=True, exist_ok=True)
        vas_resource.write_parquet(resource_path)
