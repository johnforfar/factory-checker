#!/bin/bash
# Wait for the python metadata update script to finish
echo "Monitoring update_specific_commits.py..."
while pgrep -f "update_specific_commits.py" > /dev/null; do
    sleep 10
done

echo "Metadata update complete. Moving scripts to /scripts/ folder..."
mkdir -p scripts

# Move all Python scripts
mv *.py scripts/ 2>/dev/null

# Move all Shell scripts (excluding this one if possible, but safe to move)
mv *.sh scripts/ 2>/dev/null

# Move specifically named scripts if they weren't caught
# (The glob *.py covers them)

echo "Scripts moved to factory-checker/scripts/"

