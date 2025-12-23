#!/bin/bash
# Quick test script - runs bot with limited stocks

echo "Running Stock News Scanner Bot (Test Mode)"
echo "==========================================="
echo ""

python main.py --max-stocks 5 --verbose
