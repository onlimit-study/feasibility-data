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

Like other types of packages (e.g. Rust, Python, R), the contents of the
repository *build* the final data package, but aren't the data package itself.
The repository contains the source code and raw data input, but isn't the package itself.
We need to first "compile" the code and the raw data input into the final data package.

Here are some of the steps involved in the build process:

- The raw data is pulled from the source locations during the build process,
  saved into `raw/` and processed into `staging/`. We use
  [pytask](https://pytask-dev.readthedocs.io/en/stable/) to manage this phase of
  the build process.
- The `raw/` data files are saved into the Git LFS during the build process, but
  no other data artifact is kept in the Git history.
- The metadata file is generated from the Python code into `datapackage.json`
  and the resource files are generated from the `staging/` data. The metadata
  file is the only file saved in the Git history during this phase. We use
  [Sprout](https://sprout.seedcase-project.org/) along with
  [pytask](https://pytask-dev.readthedocs.io/en/stable/) to handle this section
  of the build process.
- The data package is built into one `.tar` file that contains the metadata file
  (`datapackage.json`), `LICENSE.md`, `README.md`, and the resource files. It is
  also built into a `.zip` file with the same files except for the data. This
  `.zip` file will be what is uploaded to public archives, while the `.tar` file
  remains in the server. The `.tar` and `.zip` files are saved into a Git
  ignored `releases/` directory, with the filename being the name of the data
  package and the version number (e.g. `feasibility-data_0.1.0.tar`).

<!-- TODO: Do we also want to store the README in the `.tar` file? Any other files? -->

What this means during development is that:

- No data is saved or stored in the Git LFS. Outside of the build process,
  we treat any data pulled from sources or processed into staging or resources
  as temporary.
- Pull requests should *not* contain any changes to the `datapackage.json` file
  nor any additions of data in `raw/`, `staging/`, or `resources/`. These files
  are generated during the build process and should not be modified or added
  directly.
- Commit messages should still be written in the Conventional Commits format,
  though the specific commit types used are a bit different considering no data
  or metadata files are being modified directly. See the [release
  process](#release-process) section below for more details on commit messages
  to use.

## Release process

When committing changes, please try to follow [Conventional
Commits](https://decisions.seedcase-project.org/why-conventional-commits/) as
Git messages. Using this convention allows us to be able to automatically create
a release based on the commit message by using
[Cocogitto](https://decisions.seedcase-project.org/why-semantic-release-with-cocogitto/).
If you don't use Conventional Commits when making a commit, we will revise the
pull request title to follow that format. That's because we use squash merges
when merging pull requests, so all other commits in the pull request will be
squashed into one commit.

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
