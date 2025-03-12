#!/usr/bin/env python3
import re

# Read the file
with open('scraper.py', 'r') as file:
    content = file.read()

# 1. Fix Wikipedia citation brackets removal
# Find all instances where we get text from Wikipedia paragraphs
pattern1 = r"(first_paragraph\.get_text\(\)\.strip\(\))"
replacement1 = r"first_paragraph.get_text().strip()\n                    # Remove citation brackets with regex\n                    text = re.sub(r'\\\\[\\\\d+\\\\]|\\\\[[a-z]\\\\]|\\\\[citation needed\\\\]', '', first_paragraph.get_text().strip())"

# 2. Update Alpha Vantage API key
pattern2 = r"alpha_vantage_url = f\"https://www\.alphavantage\.co/query\?function=GLOBAL_QUOTE&symbol=\{ticker\}&apikey=demo\""
replacement2 = r"alpha_vantage_api_key = \"L9G6MGNULR85OKCN\"  # Using a dedicated API key for better results\n            alpha_vantage_url = f\"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={alpha_vantage_api_key}\""

# Apply replacements
content = re.sub(pattern1, replacement1, content)
content = re.sub(pattern2, replacement2, content)

# Write the file back
with open('scraper.py', 'w') as file:
    file.write(content)

print("Scraper.py has been updated.")