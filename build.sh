#!/bin/sh
set -eu
project_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
exec "${PYTHON:-python3}" -m build "$project_dir" "$@"
