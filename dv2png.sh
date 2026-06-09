#!/bin/bash
# dv2png launcher script

PORT=${1:-3000}  # Default to port 3000, or use first argument

# Initialize conda
source /opt/anaconda3/etc/profile.d/conda.sh

# Activate environment and launch app
conda activate bigfish_env && cd /Users/nalytorres/Documents/GitHub/dv2png/backend && PORT=$PORT python app.py
