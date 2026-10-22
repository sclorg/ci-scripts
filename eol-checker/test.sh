#!/bin/bash
set -euo pipefail
tox -e "${TOX_ENV:-py314}"
