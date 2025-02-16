#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p static
mkdir -p downloads

# Make the script executable
chmod +x vercel-build.sh 