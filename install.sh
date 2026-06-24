#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export SCRIPT_DIR

SETTINGS_PATH="$HOME/.gemini/antigravity-cli/settings.json"

# Create settings directory if it doesn't exist
mkdir -p "$(dirname "$SETTINGS_PATH")"
if [ ! -f "$SETTINGS_PATH" ]; then
    echo "{}" > "$SETTINGS_PATH"
fi

# Use Python to reliably update the settings.json file instead of jq or sed
python3 -c "
import json, sys, os

script_dir = os.environ['SCRIPT_DIR']

path = os.path.expanduser('~/.gemini/antigravity-cli/settings.json')
try:
    with open(path, 'r') as f:
        data = json.load(f)
except Exception:
    data = {}

if 'statusLine' not in data:
    data['statusLine'] = {}

data['statusLine']['type'] = 'command'
data['statusLine']['command'] = '/usr/bin/env python3 ' + os.path.join(script_dir, 'status_line.py')
data['statusLine']['enabled'] = True

with open(path, 'w') as f:
    json.dump(data, f, indent=2)
"

echo "Status line extension installed successfully!"
