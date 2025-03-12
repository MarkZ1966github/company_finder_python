#!/usr/bin/env python3

# Read the file
with open('scraper.py', 'r') as file:
    lines = file.readlines()

# Find and fix the duplicated try statement
found_try = False
for i, line in enumerate(lines):
    if "# Handle potential None result from GoogleNews" in line:
        if found_try:
            # This is the second occurrence - delete this line and the following try line
            del lines[i:i+2]
            break
        found_try = True

# Write the file back
with open('scraper.py', 'w') as file:
    file.writelines(lines)

print("Fixed duplicated try statement in scraper.py")