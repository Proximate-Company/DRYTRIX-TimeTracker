#!/bin/bash
cd /app
echo "====== Running TimeTracker Tests ======"
python -m pytest tests/ -v --tb=short
echo "====== Tests Complete. Exit Code: $? ======"

