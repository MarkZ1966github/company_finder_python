#!/bin/bash

# Fix the issue with the scraper not properly identifying companies

echo "Fixing the scraper to better identify company information..."

# Create a patch file for the scraper
cat > scraper_fix.patch << 'EOF'
--- scraper.py	2025-03-11 06:45:00.000000000 -0500
+++ scraper_new.py	2025-03-11 06:45:00.000000000 -0500
@@ -151,6 +151,11 @@
                 if first_paragraph:
                     data['overview'] = first_paragraph.get_text().strip()
                     self.logger.info(f"Found Wikipedia overview via requests: {data['overview'][:50]}..." if len(data['overview']) > 50 else data['overview'])
+                    
+                    # Check if this is about a non-company entity
+                    non_company_indicators = ['ancient', 'river', 'mythology', 'historical', 'history', 'century', 'bc', 'b.c.', 'geographical', 'geography']
+                    if any(indicator in data['overview'].lower() for indicator in non_company_indicators):
+                        self.logger.warning(f"Wikipedia article appears to be about a non-company entity (found non-company indicators)")
+                        return {}  # Return empty data to skip this irrelevant information
                     
                     # Get infobox data
                     infobox = soup.select_one('.infobox')
@@ -307,6 +312,12 @@
                 if first_paragraph:
                     data['overview'] = first_paragraph.get_text().strip()
                     self.logger.info(f"Found Wikipedia overview: {data['overview'][:50]}..." if len(data['overview']) > 50 else data['overview'])
+                    
+                    # Check if this is about a non-company entity
+                    non_company_indicators = ['ancient', 'river', 'mythology', 'historical', 'history', 'century', 'bc', 'b.c.', 'geographical', 'geography']
+                    if any(indicator in data['overview'].lower() for indicator in non_company_indicators):
+                        self.logger.warning(f"Wikipedia article appears to be about a non-company entity (found non-company indicators)")
+                        return {}  # Return empty data to skip this irrelevant information
                 
                 # Get infobox data
                 infobox = soup.select_one('.infobox')
@@ -501,7 +512,7 @@
             wiki_data = self.scrape_wikipedia(company_name)
             
             # Check if Wikipedia data appears to be about the company
-            if wiki_data and 'overview' in wiki_data:
+            if wiki_data and wiki_data.get('overview'):
                 wiki_overview = wiki_data['overview'].lower()
                 wiki_relevance_score = 0
                 
EOF

# Apply the patch
echo "Applying patch to scraper.py..."
patch -p0 < scraper_fix.patch

echo "Patch applied successfully."

# Restart the server
echo "Restarting the server..."
bash restart-server.sh