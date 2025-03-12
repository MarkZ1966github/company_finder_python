#!/usr/bin/env python3

with open('scraper.py', 'r') as file:
    content = file.read()

# Replace all instances of the problematic patterns
fixed_content = content.replace("if ',' in leader_text or '\n' in leader_text:", 
                               "if ',' in leader_text or '\\n' in leader_text:")
fixed_content = fixed_content.replace("re.split('[,\n]', leader_text)", 
                                    "re.split('[,\\\\n]', leader_text)")

with open('scraper_fixed.py', 'w') as file:
    file.write(fixed_content)

print("Fixed file saved as scraper_fixed.py")