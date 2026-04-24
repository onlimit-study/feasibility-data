@_default:
    just --list --unsorted

# Run all build-related recipes in the justfile
run-all: install-deps format-md format-python check-python check-spelling check-commits build build-website

# List all TODO items in the repository
list-todos:
  grep -R -n --exclude="*.code-snippets" --exclude="justfile" "TODO" *

# Install the pre-commit hooks
install-precommit:
  # Install pre-commit hooks
  uvx pre-commit install
  # Run pre-commit hooks on all files
  uvx pre-commit run --all-files
  # Update versions of pre-commit hooks
  uvx pre-commit autoupdate

# Install Python package dependencies
install-deps:
  uv sync --upgrade --dev --all-extras

# Check Python code with the linter for any errors that need manual attention
check-python:
  uv run ruff check .

# Reformat Python code to match coding style and general structure
format-python:
  uv run ruff check --fix .
  uv run ruff format .

# Format Markdown files
format-md:
  uvx rumdl fmt --silent

# Check the commit messages on the current branch that are not on the main branch
check-commits:
  #!/usr/bin/env bash
  branch_name=$(git rev-parse --abbrev-ref HEAD)
  number_of_commits=$(git rev-list --count HEAD ^main)
  if [[ ${branch_name} != "main" && ${number_of_commits} -gt 0 ]]
  then
    # If issue happens, try `uv tool update-shell`
    uvx --from commitizen cz check --rev-range main..HEAD
  else
    echo "On 'main' or current branch doesn't have any commits."
  fi

# Check for spelling errors in files
check-spelling:
  uv run typos

# Re-build the data package
build:
  uv run main.py

# Check for and apply updates from the template
update-from-template:
  uvx copier update --trust --defaults

# Reset repo changes to match the template
reset-from-template:
  uvx copier recopy --trust --defaults

# Build the documentation for the Data Package
build-docs:
  uv run seedcase-flower build

# Build the documentation website using Quarto
build-website: build-docs
  uv run quarto render --execute

# Preview the documentation website with automatic reload on changes
preview-website: build-docs
  uv run quarto preview --execute

# Download data dictionary from REDCap
download-data-dict:
  uv run python scripts/redcap.py
