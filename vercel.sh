#!/bin/bash

# Install Vercel CLI if not installed
if ! command -v vercel &> /dev/null; then
    npm install -g vercel
fi

# Deploy to Vercel
vercel --prod 