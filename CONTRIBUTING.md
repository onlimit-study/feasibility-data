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

## Release process

Usually the release process for other types of packages is done through a
`release.yml` GitHub workflow. But for data packages it's a bit different,
especially when there is human data involved and when the data is on secure
servers.

- Because the data is on secure servers, we can't use GitHub workflows. Which
  means we can't use a continuous release process. Instead, releases are done on
  the server through a scheduler (as a cron job) that runs on a regular basis.
- The first release happens once there is code that takes the first resource and
  its metadata from raw into its final state. The code must also be integrated
  into the `build.py` file, so that the build pipeline can run automatically.
  Note that we've already created a few releases, but we realised this process
  didn't work well for data packages and switched to this scheduled process.
- Because the release is scheduled, each pull request won't trigger a release
  anymore. Instead, a release will only be created on a schedule (if there are
  any releasable changes).

<!-- TODO: How often should we release? -->

The steps for creating a release are:

- Check the commit history since the last release for any releasable changes. If
  no releasable changes are found, then no release is created. Otherwise, the
  process continues.
- Update the version based on the commit message and save it into the
  `pyproject.toml` file using `uv version`. The `datapackage.json` version field
  uses the version in `pyproject.toml` and will be updated automatically when
  the `datapackage.json` file is (re)generated.
- Run the build process from start to end. This is described above in the [build
  process](#build-process) section.
- Generate the changelog based on the commit messages since the last release.
- Commit the changes to the `CHANGELOG.md`, `raw/` files, and `datapackage.json`
  files, then create a tag for the new version on that commit. Push to GitHub.
- Create a new GitHub release on GitHub from the new tag and changelog. Attach
  the built `.zip` file (renamed to `feasibility_data.zip`, since the tag itself
  contains the version number) to the release.

### Commit types and versions

When committing changes, please try to follow [Conventional
Commits](https://decisions.seedcase-project.org/why-conventional-commits/) as
Git messages. This convention allows us to be able to automatically create a
release based on the commit message by using
[Cocogitto](https://decisions.seedcase-project.org/why-semantic-release-with-cocogitto/).
If you don't use Conventional Commits when making a commit, we will revise the
pull request title to follow that format. That's because we use squash merges
when merging pull requests, so all other commits in the pull request will be
squashed into one commit.

Which Conventional Commit type you use depends on the content of the commit
message. We use aspects of [Data Package's semantic
versioning](https://datapackage.org/recipes/data-package-version/), where `feat`
updates the `MINOR` version, `fix` and `refactor` updates the `PATCH` version,
and any `BREAKING CHANGE` (in the commit message footer) or `<type>!` (e.g.,
`feat!`) updates the `MAJOR` version. The final format is `MAJOR.MINOR.PATCH`.

<!-- TODO: When should a "stable release" be? After all participants go through the first phases? -->

Breaking changes with the `<type>!` format only happens after the first stable
release. We define the first stable release to be when the data package has all
expected or planned resources, the metadata has been filled out, and the
participants have completed the initial, main phases of the study. Before that
point, only `MINOR` and `PATCH` changes are allowed (we remain at
`0.MINOR.PATCH`). After that point, breaking changes would be when you:

- Change the data package, resource, or column name or identifier.
- Remove a resource or column from the data package.
- Move a column into another resource.
- Change a column type (e.g. from integer to string).
- Change a column's constraints to be more restrictive (e.g. reduce the distance
  between the minimum and maximum values).
- Remove a participant's data (e.g. they request their data be deleted).
- Substantially change the meaning of the text in the metadata (e.g. a column's
  description or a resource's title).

Minor changes with the `feat` format would be:

- Add a new resource.
- Add data, either as rows or columns to an existing resource.
- Change a column's constraints to be less restrictive (e.g. increase the
  distance between the minimum and maximum values).
- Change data to reflect changes in referenced data

Patch changes with the `fix` and `refactor` formats would be:

- Correct errors in existing data, like a typo or data entry error. Depending on
  the severity of the error, this could also be a breaking change.
- Change the text of the metadata without changing the meaning, for example
  fixing typos, grammatical errors, or clarifying the text without changing its
  meaning.

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
