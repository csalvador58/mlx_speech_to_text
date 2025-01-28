#!/bin/bash

# Ensure script exits on error
set -e

# Print and execute the directory command
echo "Setting SCRIPT_DIR to current directory..."
echo "SCRIPT_DIR=\"\$( cd \"\$( dirname \"\${BASH_SOURCE[0]}\" )\" && pwd )\""
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "SCRIPT_DIR is: $SCRIPT_DIR"

# Change to the script directory
echo -e "\nChanging to script directory..."
cd "$SCRIPT_DIR"

# Print and execute the activate command
echo -e "\nActivating virtual environment..."
echo "source \"$SCRIPT_DIR/.venv/bin/activate\""
source "$SCRIPT_DIR/.venv/bin/activate"

# Run the application
echo -e "\nRunning application..."
uv run src/main.py --copy

# Deactivate the virtual environment when done
echo -e "\nDeactivating virtual environment..."
deactivate