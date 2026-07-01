# Contributing

## Flow of data

### REDCap

The data flows directly from the REDCap API into `raw/redcap/` as a JSON file
with a timestamp appended to the filename. Every time the data is pulled from
REDCap, a new JSON file is created in `raw/redcap/` with the current timestamp.

Using code writing in `src/feasibility_data/data/redcap/<resource>.py`, each raw
JSON file is processed into `staging/redcap/<resource>/<timestamp>.parquet`.
There should be a 1-to-1 mapping between the raw JSON's timestamp and the staged
resource Parquet file's timestamp.

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
