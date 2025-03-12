#!/usr/bin/env python3
import re

# Read the file
with open('scraper.py', 'r') as file:
    content = file.read()

# Add improved leadership information extraction
leadership_extraction_code = '''
    def extract_leadership_from_website(self, soup):
        """Extract leadership information from website HTML"""
        leadership = []
        leadership_keywords = ['leadership', 'management', 'team', 'executives', 'founders', 'board', 'directors', 'ceo', 'chief', 'president', 'founder']
        
        # Look for leadership sections
        leadership_section = soup.find(id=lambda i: i and any(keyword in i.lower() for keyword in leadership_keywords))
        if not leadership_section:
            leadership_section = soup.find(class_=lambda c: c and any(keyword in c.lower() for keyword in leadership_keywords))
        
        # Try by content
        if not leadership_section:
            leadership_section = soup.find(lambda tag: tag.name and tag.name.lower() in ['h1', 'h2', 'h3', 'h4'] and 
                                          any(word in tag.get_text().lower() for word in leadership_keywords))
            if leadership_section:
                # Get the next sibling elements that might contain the team info
                leadership_section = leadership_section.find_next(['div', 'section', 'ul'])
        
        if leadership_section:
            # Try to find leadership elements - often in headings followed by descriptions
            # Pattern 1: h3/h4 with name followed by position in p or div
            for name_elem in leadership_section.find_all(['h3', 'h4', 'h5', 'strong', 'b']):
                name = name_elem.get_text().strip()
                position_elem = name_elem.find_next(['p', 'div', 'span'])
                position = position_elem.get_text().strip() if position_elem else 'Leadership'
                
                if name and len(name) < 50:  # Reasonable length for a name
                    # Check if this looks like a person name (not a heading like "Our Team")
                    if not any(keyword in name.lower() for keyword in ['team', 'leadership', 'management', 'board', 'directors']):
                        leadership.append({
                            'name': name,
                            'position': position
                        })
                        self.logger.info(f"Found leader from website: {name} ({position})")
            
            # If no leaders found, try other common patterns
            if not leadership:
                # Look for list items that might contain leadership info
                for item in leadership_section.find_all('li'):
                    text = item.get_text().strip()
                    # Try to separate name and position
                    if ',' in text or '-' in text or '–' in text:
                        parts = re.split('[,\\\\-–]', text, 1)
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            position = parts[1].strip()
                            leadership.append({
                                'name': name,
                                'position': position
                            })
                            self.logger.info(f"Found leader from list: {name} ({position})")
            
            # If still no leaders found, try looking for structured data
            if not leadership:
                for card in leadership_section.find_all(['div', 'article', 'section']):
                    # Look for name and position within the card
                    name_elem = card.find(['h3', 'h4', 'h5', 'strong', 'b'])
                    if name_elem:
                        name = name_elem.get_text().strip()
                        position_elem = card.find(['p', 'div', 'span'])
                        position = position_elem.get_text().strip() if position_elem else 'Leadership'
                        
                        if name and len(name) < 50 and name != position:  # Avoid duplicates
                            leadership.append({
                                'name': name,
                                'position': position
                            })
                            self.logger.info(f"Found leader from card: {name} ({position})")
        
        # If we still don't have leadership, try a more general approach
        if not leadership:
            # Look for CEO, President, Founder keywords across the page
            executive_keywords = ['ceo', 'chief executive', 'president', 'founder', 'chairman', 'cto', 'cfo', 'chief financial', 'chief technology']
            for keyword in executive_keywords:
                # Find elements that contain these keywords
                elements = soup.find_all(lambda tag: tag.name and tag.string and keyword in tag.get_text().lower())
                for elem in elements:
                    text = elem.get_text().strip()
                    # Try to extract name and position
                    # Common pattern: "John Doe, CEO" or "CEO: John Doe" or "CEO John Doe"
                    if ':' in text:
                        parts = text.split(':', 1)
                        if keyword in parts[0].lower():  # "CEO: John Doe"
                            position = parts[0].strip()
                            name = parts[1].strip()
                        else:  # "John Doe: CEO"
                            name = parts[0].strip()
                            position = parts[1].strip()
                        leadership.append({
                            'name': name,
                            'position': position
                        })
                        self.logger.info(f"Found leader from keyword search: {name} ({position})")
                    elif ',' in text:
                        parts = text.split(',', 1)
                        if keyword in parts[1].lower():  # "John Doe, CEO"
                            name = parts[0].strip()
                            position = parts[1].strip()
                            leadership.append({
                                'name': name,
                                'position': position
                            })
                            self.logger.info(f"Found leader from keyword search: {name} ({position})")
        
        return leadership
'''

# Find the right place to insert this method (before the scrape_website method)
pattern = r"def scrape_website\(self, website\):"
replacement = leadership_extraction_code + "\n    def scrape_website(self, website):"

# Replace the old leadership extraction code with a call to the new method
old_leadership_code = r"# Try to find leadership information.*?data\['leadership'\] = \[\].*?self\.logger\.info\(f\"Found leader from card: \{name\} \(\{position\}\).*?\)"
new_leadership_code = "# Extract leadership information\n                data['leadership'] = self.extract_leadership_from_website(soup)\n                self.logger.info(f\"Found {len(data['leadership'])} leadership team members\")"

# Apply replacements
content = re.sub(pattern, replacement, content, flags=re.DOTALL)
content = re.sub(old_leadership_code, new_leadership_code, content, flags=re.DOTALL)

# Write the file back
with open('scraper.py', 'w') as file:
    file.write(content)

print("Leadership extraction has been improved in scraper.py.")