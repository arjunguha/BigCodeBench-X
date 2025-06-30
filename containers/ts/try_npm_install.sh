#!/bin/bash

cd /root

# Check if any arguments were provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 package1 [package2 package3 ...]"
    exit 1
fi

mkdir -p /npm_logs

# Iterate through all provided package names
for PACKAGE_NAME in "$@"; do
    echo "Installing $PACKAGE_NAME..."
    npm install "$PACKAGE_NAME" &> /npm_logs/${PACKAGE_NAME//\//_}.log
    if [ $? -ne 0 ]; then
        echo "FAILED: $PACKAGE_NAME" >> install_log.txt
    else
        echo "SUCCESS: $PACKAGE_NAME" >> install_log.txt
    fi
done
