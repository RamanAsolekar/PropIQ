#!/bin/bash
# PropIQ Backend — One-command setup
# Run: chmod +x setup.sh && ./setup.sh

set -e
echo "======================================"
echo "  PropIQ — Backend Setup"
echo "======================================"

# 1. Python deps
echo ""
echo "[1/4] Installing dependencies..."
pip install -r requirements.txt -q

# 2. Generate training data
echo ""
echo "[2/4] Generating synthetic training data..."
python -m app.ml.data_generator

# 3. Train model
echo ""
echo "[3/4] Training XGBoost valuation model..."
python -m app.ml.valuation_model

# 4. Run tests
echo ""
echo "[4/4] Running tests..."
python -m pytest tests/test_day1.py -v -k "circle_rate or pdf or cv" --no-header

echo ""
echo "======================================"
echo "  Setup complete!"
echo "  Start API:  uvicorn app.main:app --reload --port 8000"
echo "  Swagger UI: http://localhost:8000/docs"
echo "======================================"