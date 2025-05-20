#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <results.jsonl>"
    exit 1
fi


echo -n "$1, "
jq -r -s '([.[] | select(.exit_code == 0)] | length) as $success | ($success  / length) | . * 100 |round / 100' $1
