#!/bin/bash
set -e  

echo "▶ Step 1: get_library.py"
python3 src/get_library.py

echo "▶ Step 2: gemini_repair.py"
python3 src/gemini_repair.py

echo "▶ Step 3: write_library.py"
python3 src/write_library.py

echo "✅ All done!"
