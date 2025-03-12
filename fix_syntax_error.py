#!/usr/bin/env python3
import re

# Read the file
with open('scraper.py', 'r') as file:
    content = file.read()

# Fix the citation brackets removal code
pattern = r"first_paragraph\.get_text\(\)\.strip\(\)\n                    # Remove citation brackets with regex\n                    text = re\.sub\(r'\\\\\\[\\\\d\+\\\\\\]\\|\\\\\\[a-z\\\\\\]\\|\\\\\\[citation needed\\\\\\]', '', first_paragraph\.get_text\(\)\.strip\(\)\)"
replacement = r"first_paragraph.get_text().strip()"

# Apply replacements
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Add citation bracket removal after the assignments
pattern1 = r"(data\['overview'\] = first_paragraph\.get_text\(\)\.strip\(\))"
replacement1 = r"data['overview'] = first_paragraph.get_text().strip()\n                    # Remove citation brackets with regex\n                    data['overview'] = re.sub(r'\\[\\d+\\]|\\[[a-z]\\]|\\[citation needed\\]', '', data['overview'])"

pattern2 = r"(data\['overview'\] = first_paragraph\.get_text\(\)\.strip\(\)\n                                self\.logger\.info)"
replacement2 = r"data['overview'] = first_paragraph.get_text().strip()\n                                # Remove citation brackets with regex\n                                data['overview'] = re.sub(r'\\[\\d+\\]|\\[[a-z]\\]|\\[citation needed\\]', '', data['overview'])\n                                self.logger.info"

# Apply replacements
content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

# Write the file back
with open('scraper.py', 'w') as file:
    file.write(content)

print("Fixed syntax error in scraper.py.")