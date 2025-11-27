#!/bin/bash

echo "Starting Swine Breeding Detection System (24/7 Mode)..."
echo "Press [CTRL+C] to stop."

while true; do
    echo "----------------------------------------"
    echo "Launching detector at $(date)..."
    
    # Run the detector
    uv run detector.py
    
    # Check exit code
    EXIT_CODE=$?
    echo "Detector stopped with exit code $EXIT_CODE."
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Clean exit. Stopping loop."
        break
    else
        echo "⚠️ Crash or error detected. Restarting in 10 seconds..."
        sleep 10
    fi
done
