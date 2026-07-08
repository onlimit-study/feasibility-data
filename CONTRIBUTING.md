# Contributing

## Flow of data

### REDCap

The data flows directly from the REDCap API into `raw/redcap/` as a CSV file
with a timestamp appended to the filename. Every time the data is pulled from
REDCap, a new CSV file is created in `raw/redcap/` with the current timestamp.

Using code written in `src/feasibility_data/data/redcap/<resource>.py`, each raw
CSV file is processed into a collection of
`staging/redcap/<resource>/<timestamp>.parquet` files. There should be a 1-to-1
mapping between the raw CSV's timestamp and the staged resource Parquet file's
timestamp.

If metadata drifts over time, errors will happen when processing the older raw
CSV files using the newer metadata. This is expected and desirable behaviour as
it:

- Informs us that we need to update or resolve the older data to match the newer
  metadata.
- Helps ensure transparency and a record of how the data has changed over time
  and how we've fixed it.
- Ensures that all files in `staging/` are aligned, as Sprout takes all files in
  `staging/` and converts them into a single resource. So they must always match
  together.
- Matches the behaviour of our pipelines from other sources. While REDCap stores
  data for up to 5 years, other sources of data for ON LiMiT have much shorter
  retention periods. So previously pulled raw data in this repository may be the
  only copy of that data available to us. Which means we need to us all raw data
  when processing into `staging/` and eventually into `resources/`.

There are specific things to note about the REDCap data:

- Fields ending in `_id` are primary/foreign keys.
- Fields that contain `admin` are excluded from the data package.

When processing the data, each resource should (almost always) contain a
`participant_id` and a `visit_id` field.

## Layout of `src/`

Similar to how `raw/` and `staging/` are organized, the Python files within
`src/` are organized at the top level by `data` and `metadata`, then by source
of the original data, and finally by the eventual resource name. The structure
under `src/feasibility_data/` is:

- `metadata/<source>/<resource>.py`: Python files within this directory contain
  functions that are used to convert the raw dictionaries into the final
  `datapackage.json` metadata file. Functions within these modules can be named
  without needing to state the source or resource (as the module path already
  contains that information). For example, `metadata/redcap/vas.py` would
  contain the functions for processing the metadata for the VAS resource from
  the REDCap source.
- `data/<source>/<resource>.py`: Same with the metadata files, but these contain
  functions for taking the original raw data and converting them into the
  `staging/` folder. Unlike the metadata above, raw data goes into `staging/`
  first before being processed into the final data resource as Sprout needs to
  run checks against the metadata before converting it into the final data
  resource.
- `common/`: Contains functions that are used across multiple resources. The
  names of the Python files within are not standardized, but they should be
  descriptive of the overall functionality they provide within.
- `build.py`: This file lists all the functions (as
  [pytask](https://pytask-dev.readthedocs.io/en/stable/) tasks) that are needed
  to take the raw data and raw dictionaries and turn it all into a final data
  package.

## Writing Python code

- Each "public" function should be at the top of the module file, with "private"
  (prefixed with `_`) functions below them.
- Classes, either public or private, go at the top of the file.
