# Contributing

## :bug: Issues and bugs

The easiest way to contribute is to report issues or bugs that you might find
while using feasibility-data. You can do this by creating a new issue on our
GitHub repository.

## :pencil2: Adding or modifying content

If you would like to contribute content, please check out our
[guidebook](https://guidebook.seedcase-project.org/) for more specific details
on how we work and develop. It is a regularly evolving document, so is at
various states of completion.

To contribute to feasibility-data, you first need to install
[uv](https://docs.astral.sh/uv/) and
[justfile](https://just.systems/man/en/packages.html). We use uv and justfile to
manage our project, such as to run checks on the data package and build the
website. Both the uv and justfile websites have a more detailed guide on using
uv, but below are some simple instructions to get you started.

It's easiest to first [install
uv](https://docs.astral.sh/uv/getting-started/installation/) and then install
justfile with uv. Once you've installed uv, install justfile by running:

```bash
uv tool install rust-just
```

We keep all our development workflows in the `justfile`, so you can explore it
to see what commands are available. To see a list of commands available, run:

```bash
just
```

As you contribute, make sure your changes will pass our tests by opening a
terminal so that the working directory is the root of this project
(`feasibility-data/`) and running:

```bash
just run-all
```

## Build process

We primarily follow the build process described in our [Building Data
Packages](https://data-pkg-guide.seedcase-project.org/) guide, in the chapter on
the [build process](https://data-pkg-guide.seedcase-project.org/docs/build/).

The contents of this repository *build* the final data package, but aren't the
data package itself. The repository only contains the source code and raw data
input. We first need to build the actual data package by running using the set
of justfile recipes. We have one main recipe called and several helper recipes:

- `just build-package` builds the data package into `.tar` and `.zip` files in
  the `releases/` folder.
- `just build-metadata` is a helper to rebuild the metadata files if, e.g. you
  want to test out how the metadata will look like in the website.
- `just build-raw` is a helper to download the raw data from the source
  locations, e.g. REDCap. We use this in order to create PRs that update the
  data in `raw/`, since that is the only data we store in the Git LFS
  (`staging/` and `resources/` are not saved, as described in the guide). This
  runs the [pytask](https://pytask-dev.readthedocs.io/en/stable/) 'raw' tasks.
- `just build-staging` is a helper to process the raw data into `staging/`. This
  runs the [pytask](https://pytask-dev.readthedocs.io/en/stable/) 'staging'
  tasks.
- `just build-resources` is a helper to process `staging/` into the final
  `resources/`.

Some things to note that during the build process:

- No data is saved or stored in Git LFS. We treat any data pulled from sources
  or processed into staging or resources as temporary.
- Pull requests should *not* contain any changes to the `datapackage.json` file
  or any additions of data in `raw/`, `staging/`, or `resources/`.
- Commit messages should still be written in the Conventional Commits format.
  See the [commits
  section](https://data-pkg-guide.seedcase-project.org/docs/release#commits) of
  the guide for details.

During development, saving raw data in `raw/` into the Git LFS store should be
intentional and should only be done within an explicit and atomic pull request.
That way we can control what commit type is used based on what actually happens
in the data (e.g. a fix or new data).

## Release process

We primarily follow the release process described in our [Building Data
Packages](https://data-pkg-guide.seedcase-project.org/) guide, in the chapter on
the [release
process](https://data-pkg-guide.seedcase-project.org/docs/release/).

From the guide, we use the manual release process that is defined within the
`justfile` as `just release`. A few notes about the release process.

- We don't publicly upload any data, only metadata (e.g. by building it into a
  website).
- We run the release process whenever we decide, usually whenever there have
  been updates to the source data or if there have been any corrections or fixes
  to the data or metadata.
- The first *stable* release (version `1.0.0`) happens when the final
  participant has their final data collected. Any release before reflects an
  incomplete state and the data should **not** be depended on for formal
  analysis.

To create a release, you just need to run `just release`. It will ask for
confirmation to run it and then will run all build steps before starting the
release process. The final output of the release process is the files created
from the build process (described [above](#build-process)), a Git tag, updated
`CHANGELOG.md`, and a generated `.tar` and `.zip` file in `releases/`.

While we manually run the `just release` recipe, if the commits haven't followed
the Conventional Commits style, no release will be created. See more details in
the [commits
section](https://data-pkg-guide.seedcase-project.org/docs/release#commits) of
the guide.

## :file_folder: Explanation of files and folders

This is a brief description of some of the files in this repository.

- `.copier-answers.yml`: Contains the answers you gave when copying the project
  from the template. **You should not modify this file directly.**
- `.github/`: Contains GitHub-specific files, such as issue and pull request
  templates, workflows,
  [dependabot](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart-guide)
  configuration, pull request templates, and a
  [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
  file.
- `_quarto.yml`: Quarto configuration file for the website, including settings
  for the website, such as the theme, navigation, and other options.
- `_metadata.yml`: Quarto metadata file for the website, including information
  about the project, such as the titles and GitHub names.
- `.gitignore`: This ignore file tells Git which files to not track. Unless you
  know what you are doing, it's best to not touch this file.
- `.pre-commit-config.yaml`: [Pre-commit](https://pre-commit.com/) configuration
  file for managing and running checks before each commit.
- `.config/`: Contains configuration files for various tools used in the
  project, such as:
  - `typos.toml`: [typos](https://github.com/crate-ci/typos) spell checker
    configuration file.
  - `rumdl.toml`: [rumdl](https://rumdl.dev) configuration file for formatting
    Markdown files in the project.
  - `cog.toml`: [Cocogitto](https://docs.cocogitto.io) configuration file for
    managing versions.
  - `cliff.toml`: [git-cliff](https://git-cliff.org) configuration file for
    creating the changelog.
  - `ruff.toml`: [Ruff](https://github.com/charliermarsh/ruff) configuration
    file for linting and formatting Python code.
- `.editorconfig`: Editor configuration file for
  [EditorConfig](https://editorconfig.org/) to maintain consistent coding styles
  across different editors and IDEs.
- `CITATION.cff`: Structured citation metadata for your project when archived on
  [Zenodo](https://zenodo.org/) and used by GitHub to display the citation
  information on the repository page. This is used to add the metadata to Zenodo
  when a GitHub release has been uploaded to Zenodo.
- `justfile`: [`just`](https://just.systems/man/en/) configuration file for
  scripting project tasks.
- `CHANGELOG.md`: Changelog file for tracking changes in the project.

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

#### REDCap metadata files

Before we can extract properties from the data downloaded from REDCap, we have
to tidy the data and split it into separate files by resource. To do this, we
use the following metadata files downloaded from REDCap:

- `field_metadata.json` (REDCap API `content` value: `metadata`): The list of
  all fields across all forms in the study. We use this to find which fields
  belong to which form.
- `event_metadata.json` (REDCap API `content` value: `formEventMapping`): The
  list of all form-event pairs. We use this to determine which forms are filled
  in at which events.
- `repeating_forms_metadata.json` (REDCap API `content` value:
  `repeatingFormsEvents`): The list of all form-event pairs that includes only
  forms that can repeat. We use this to identify which forms can repeat and
  therefore which derived resources must include a `submission_id` to tell apart
  different submissions for the same participant at the same data collection
  point.

See the [Glossary](#glossary) for a definition of terms.

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
- In either the `data/` or `metadata/` directories, files named `*/core.py`
  contain functions that do general processing tasks related to the parent
  folder name. For example, `metadata/core.py` contains functions for top-level
  metadata processing that is for general metadata, but not strictly tied to any
  given source or resource, such as data package-level metadata. Meanwhile,
  `data/redcap/core.py` contains functions for processing REDCap data that is
  *not* specific to any resource. This `core.py` file can be treated like the
  `__init__.py` file. We don't use `__init__.py` files to store functions as the
  semantic meaning of `__init__.py` is to initialise the folder as part of the
  package. The semantic meaning of `core.py` is to be a collection of functions
  that are used in its parent source/resource folder.
- `common/`: Contains functions that are used across *all* (or many) Python
  files, between metadata and data or between sources/resources. This is not the
  same as the `**/core.py` files that are *specific* to the particular source or
  resource. The names of the Python files within are not standardized, but they
  should be descriptive of the overall functionality they provide within. An
  advantage of keeping common functions in one location is that it makes it
  easier for us to identify if any of these functions belong in their own
  package.
- `build.py`: This file lists all the functions (as
  [pytask](https://pytask-dev.readthedocs.io/en/stable/) tasks) that are needed
  to take the raw data and raw dictionaries and turn it all into a final data
  package. We keep all tasks in this file to make it easier to track, review,
  and update the full build process in one location.

Similar to a Python package, all Python files must only contain functions and/or
classes and not be called directly. Functions are kept small and focused, with a
narrow scope and clear input and output (with type hints, ideally using custom
types). The only exception is the `build.py` file that has the pytask tasks.
This file is used to build up all the smaller functions into specific tasks.
These tasks have input/output that matches the style of pytask and can be larger
and more complex than the non-build functions.

## Writing Python code

- Each "public" function should be at the top of the module file, with "private"
  (prefixed with `_`) functions below them.
- Classes, either public or private, go at the top of the file.

## Glossary

- Form: In REDCap, a form or instrument is a collection of related fields that
  record information about a participant, such as demographics, laboratory
  measurements, or questionnaire responses. Forms may be completed either by
  participants (as surveys) or by members of the study team. Every field belongs
  to exactly one form and field names are unique across all forms.
- Event: In REDCap, an event is a scheduled data collection point in a
  longitudinal study, such as Prescreening, Visit 1, or Phase 1. It represents a
  planned stage of the study when data is collected from a participant (rather
  than the date and time when data is entered into REDCap). One or more forms
  can be assigned to each event to collect different kinds of information about
  the participant.
- Repeating form: In REDCap, a repeating form is a form that can be completed
  multiple times for the same participant within the same event. Each submission
  represents a separate instance of the form for that participant and event. For
  example, the Phase 1 Dietary Deviations form is a repeating form because a
  participant can report multiple deviations during Phase 1 of the study.
