#!/usr/bin/env python3

def clean_wikipedia_text(text):
    """Remove citation brackets from Wikipedia text"""
    import re
    return re.sub(r'\[\d+\]|\[[a-z]\]|\[citation needed\]', '', text)

# Update the scraper.py file to use this function
with open('scraper.py', 'r') as file:
    lines = file.readlines()

# Find where we need to add the function
for i, line in enumerate(lines):
    if "def __init__(self):" in line:
        # Add the function just before __init__
        lines.insert(i, """    @staticmethod
    def clean_wikipedia_text(text):
        \"\"\"Remove citation brackets from Wikipedia text\"\"\"
        import re
        return re.sub(r'\\[\\d+\\]|\\[[a-z]\\]|\\[citation needed\\]', '', text)
        
""")
        break

# Find where we extract Wikipedia text and apply the cleaning
for i, line in enumerate(lines):
    if "data['overview'] = first_paragraph.get_text().strip()" in line:
        # Replace with a version that cleans the text
        lines[i] = lines[i].replace(
            "data['overview'] = first_paragraph.get_text().strip()",
            "data['overview'] = self.clean_wikipedia_text(first_paragraph.get_text().strip())"
        )

# Write the file back
with open('scraper.py', 'w') as file:
    file.writelines(lines)

print("Added Wikipedia text cleaning function to scraper.py")