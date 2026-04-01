#!/bin/bash
# Installation script for Mac / Linux

PLUGIN_DIR="$HOME/.claude/plugins/repos/claude-code-tracker"

# Clone or update
if [ -d "$PLUGIN_DIR" ]; then
  echo "Updating existing installation..."
  git -C "$PLUGIN_DIR" pull
else
  echo "Installing claude-code-tracker..."
  git clone https://github.com/55onurisik/claude-code-tracker "$PLUGIN_DIR"
fi

echo ""
echo "Done! Restart Claude Code to activate the plugin."
echo ""
echo "Test with: /token-tracker:stats"
