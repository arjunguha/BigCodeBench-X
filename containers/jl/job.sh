#!/bin/bash
# Usage:
#
#     ./script.sh LINE_NUMBER COMPLETIONS_JSONL
#
# This runs the container on a single completion.
#
# To run on several completions in parallel:
#
#     LINES=$(wc -l < COMPLETIONS_JSONL)
#     parallel --bar -j20 ./script.sh COMPLETIONS_JSONL ::: $(seq LINES)
#
# The constant 20 runs 20 in parallel. Adjust it as appropriate.
COMPLETIONS_JSONL=$1
LINE_NUMBER=$2
sed -n "${LINE_NUMBER}p" ${COMPLETIONS_JSONL} | podman run --rm -i ghcr.io/arjunguha/bcb_multipl-jl
