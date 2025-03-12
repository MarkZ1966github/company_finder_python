#!/usr/bin/env python3
import re

# Read the file
with open('scraper.py', 'r') as file:
    content = file.read()

# Add the fallback methods for news
news_methods = '''
    def _try_bing_news_fallback(self, company_name, data):
        """Try to get news from Bing News"""
        self.logger.info(f"Trying Bing News fallback for {company_name}")
        fallback_url = f"https://www.bing.com/news/search?q={company_name.replace(' ', '+')}"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(fallback_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract news articles from Bing News
                news_cards = soup.select('.news-card')
                for i, card in enumerate(news_cards[:5]):
                    try:
                        title_elem = card.select_one('.title')
                        link_elem = card.select_one('a')
                        source_elem = card.select_one('.source')
                        description_elem = card.select_one('.snippet')
                        
                        title = title_elem.text.strip() if title_elem else 'No title available'
                        link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''
                        source = source_elem.text.strip() if source_elem else 'Unknown Source'
                        description = description_elem.text.strip() if description_elem else 'No description available'
                        
                        # Add article to results
                        data['articles'].append({
                            'title': title,
                            'link': link,
                            'date': datetime.datetime.now().strftime('%Y-%m-%d'),  # Use current date as fallback
                            'source': source,
                            'description': description
                        })
                        self.logger.info(f"Added news article from Bing: {title}")
                    except Exception as card_error:
                        self.logger.error(f"Error processing Bing article {i}: {card_error}")
                        continue
        except Exception as fallback_error:
            self.logger.error(f"Bing news fallback failed: {fallback_error}")
    
    def _try_google_news_fallback(self, company_name, data):
        """Try to get news from Google News search"""
        self.logger.info(f"Trying Google News search fallback for {company_name}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            search_url = f"https://www.google.com/search?q={company_name}+news&tbm=nws"
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                news_divs = soup.select('div.SoaBEf')
                if not news_divs:  # Try alternative selectors
                    news_divs = soup.select('div.WlydOe')
                
                for i, div in enumerate(news_divs[:5]):
                    try:
                        title_elem = div.select_one('div.mCBkyc')
                        if not title_elem:
                            title_elem = div.select_one('h3')
                        
                        link_elem = div.select_one('a')
                        source_elem = div.select_one('.CEMjEf')
                        if not source_elem:
                            source_elem = div.select_one('.UPmit')
                        
                        description_elem = div.select_one('.GI74Re')
                        if not description_elem:
                            description_elem = div.select_one('div.Y3v8qd')
                        
                        title = title_elem.text.strip() if title_elem else 'No title available'
                        link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''
                        source = source_elem.text.strip() if source_elem else 'Unknown Source'
                        description = description_elem.text.strip() if description_elem else 'No description available'
                        
                        # Add article to results
                        data['articles'].append({
                            'title': title,
                            'link': link,
                            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
                            'source': source,
                            'description': description
                        })
                        self.logger.info(f"Added news article from Google search: {title}")
                    except Exception as div_error:
                        self.logger.error(f"Error processing Google news div {i}: {div_error}")
                        continue
        except Exception as google_error:
            self.logger.error(f"Google news search failed: {google_error}")
'''

# Find the scrape_news method and add our new methods after it
pattern = r"def scrape_news\(self, company_name\):.*?return data\n"
replacement = r"\g<0>" + news_methods + "\n"

# Apply replacements
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Modify the existing scrape_news method to use our new fallback methods
pattern = r"# If GoogleNews fails, try a fallback method.*?self\.logger\.error\(f\"Fallback news method failed: \{fallback_error\}\"\)"
replacement = r"# If GoogleNews fails, try a fallback method\n            if not data['articles']:\n                self.logger.warning(\"GoogleNews returned no articles, trying fallback methods\")\n                # Try multiple fallback methods\n                self._try_bing_news_fallback(company_name, data)\n                \n                # If still no articles, try Google News search\n                if not data['articles']:\n                    self._try_google_news_fallback(company_name, data)\n        \n        except Exception as e:\n            self.logger.error(f\"Error scraping news for {company_name}: {e}\")\n            # Try fallback on any exception\n            self._try_bing_news_fallback(company_name, data)\n            if not data['articles']:\n                self._try_google_news_fallback(company_name, data)"

# Apply replacements
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the file back
with open('scraper.py', 'w') as file:
    file.write(content)

print("Added improved news fallback methods to scraper.py")