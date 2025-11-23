#!/bin/bash
# 🚨 AWS SageMaker Cost Scanner - Quick CLI Wrapper
# Usage: ./scan_sagemaker_costs.sh [scan|cleanup] [region]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/cost_estimator_remove_resource.py"

# Default action
ACTION="--scan"
REGION=""

# Parse arguments
if [ "$1" = "cleanup" ]; then
    ACTION="--cleanup"
elif [ "$1" = "scan" ] || [ -z "$1" ]; then
    ACTION="--scan"
fi

# Region argument
if [ -n "$2" ]; then
    REGION="--region $2"
fi

echo "🚨 AWS SageMaker Cost Scanner"
echo "================================"
echo "Action: $ACTION"
if [ -n "$REGION" ]; then
    echo "Region: $2"
fi
echo "================================"
echo ""

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check for virtual environment
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    echo "🐍 Using virtual environment Python"
    PYTHON_CMD="$VENV_PYTHON"
else
    echo "🐍 Using system Python"
    PYTHON_CMD="python3"
fi

# Run the Python script
$PYTHON_CMD "$PYTHON_SCRIPT" $ACTION $REGION

echo ""
echo "✅ Scan complete!"
echo ""
echo "💡 Quick commands:"
echo "  ./scan_sagemaker_costs.sh scan          # Scan only"
echo "  ./scan_sagemaker_costs.sh cleanup       # Scan and cleanup"
echo "  ./scan_sagemaker_costs.sh scan us-west-2 # Specific region"