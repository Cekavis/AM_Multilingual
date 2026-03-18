#!/bin/bash
set -e  

echo "▶ Step 1: get_library.py"
uv run -m src.get_library

echo "▶ Step 2: gemini_repair.py"
uv run -m src.gemini_repair

echo "▶ Step 3: write_library.py"
uv run -m src.write_library

echo "✅ All done!"
