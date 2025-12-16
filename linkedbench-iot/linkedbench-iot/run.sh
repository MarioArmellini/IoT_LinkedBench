#!/bin/bash
# Quick run script for LinkedBench

cd "$(dirname "$0")"

echo "Starting LinkedBench IoT System..."
echo "Press Ctrl+C to stop"
echo ""

python3 linkedbench.py "$@"
