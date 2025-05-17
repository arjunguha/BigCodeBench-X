#!/bin/bash
# TensorFlow does not support Python 3.10 as of May 14 2025.
apt-get update && apt-get install -y --no-install-recommends build-essential

uv venv -p 3.10 /venv
source /venv/bin/activate
uv pip install -r /requirements.txt
