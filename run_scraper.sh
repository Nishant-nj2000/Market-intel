#!/usr/bin/env bash
set -e
export PYTHONPATH=$(pwd)/src
python3 -m src.main --mode both --config config.yaml