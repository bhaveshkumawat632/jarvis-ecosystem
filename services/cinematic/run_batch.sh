#!/bin/bash

cd /home/junglee01/jarvis_universal

# Ensure output directory exists
mkdir -p outputs

echo "Waiting for the first video (Black Holes) to finish..."
while pgrep -f "10 Mind Blowing Facts About Black Holes" > /dev/null; do
    sleep 30
done
echo "First video finished. Starting the sequential generation..."

topics=(
    "10 Mysteries of the Universe Never Solved"
    "How Ancient Egyptians Built the Pyramids"
    "10 Facts About Deep Ocean Creatures"
    "The Rise and Fall of Roman Empire"
    "10 Unsolved Mysteries of Human Brain"
    "How Artificial Intelligence Will Change 2030"
    "10 Strange Planets Beyond Our Solar System"
    "The Secret History of World War 2"
    "10 Amazing Facts About Quantum Physics"
)

for topic in "${topics[@]}"; do
    echo "======================================"
    echo "Starting generation for: $topic"
    echo "======================================"
    python3 app.py --topic "$topic" --duration 8 --quality 1080p --ai-video
    echo "Finished generation for: $topic"
    echo ""
done

echo "All videos generated successfully."
