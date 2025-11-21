#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "Compiling Document Ingestion Pipeline"
echo "============================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Compiling pipeline.py file to YAML"
echo "   Output: pipeline.yaml"
echo ""

python pipeline.py || {
    echo "Pipeline code to YAML compilation failed!"
    exit 1
}

echo ""
echo "============================================"
echo "compilations successful!"
echo "============================================"
echo ""
echo "Files created:"
ls -lh pipeline.yaml
echo ""
echo "Deploy Pipelines in RHOAI"
echo "  1. Open RHOAI dashboard"
echo "  2. Navigate to: Data Science Pipelines → Import Pipeline"
echo "  3. Upload: pipeline.yaml"
echo ""

