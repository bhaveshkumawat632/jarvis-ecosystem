#!/bin/bash

# स्टेप 1: GPU टेस्ट
echo "Running GPU Benchmark..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected"
    nvidia-smi
else
    echo "WARNING: NVIDIA GPU not detected"
    echo "Switching to CPU-safe mode"
fi

# स्टेप 2: रेंडर बेंचमार्क
echo "Running Render Benchmark..."
python3 benchmarks/concurrent_workflow_test.py
if [ $? -ne 0 ]; then
    echo "Render Benchmark Failed"
    exit 1
fi

# स्टेप 3: रिटेंशन वैलिडेशन
echo "Running Retention Validation..."
python3 analytics/validation/retention_validator.py
if [ $? -ne 0 ]; then
    echo "Retention Validation Failed"
    exit 1
fi

# स्टेप 4: आर्थिक मार्जिन कैलकुलेशन
echo "Running Financial Margin Calculation..."
python3 app/core/financials/margin_calculator.py
if [ $? -ne 0 ]; then
    echo "Financial Margin Calculation Failed"
    exit 1
fi

# स्टेप 5: चेओस टेस्टिंग
echo "Running Chaos Test..."
python3 benchmarks/chaos_tester.py
if [ $? -ne 0 ]; then
    echo "Chaos Test Failed"
    exit 1
fi

echo "All tests passed successfully. Check details above for any issues."
