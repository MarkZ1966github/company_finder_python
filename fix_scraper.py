import re

def add_guess_website_method():
    return '''
    def guess_website_from_name(self, company_name):
        """Try to guess a company website from its name"""
        if not company_name:
            return None
            
        # Remove common company suffixes
        name = company_name.lower()
        for suffix in [' inc', ' corp', ' corporation', ' llc', ' ltd', ' limited', ' company', ' co', ' group']:
            name = name.replace(suffix, '')
            
        # Clean up the name for a domain
        name = name.strip().replace(' ', '').replace(',', '').replace('.', '').replace('-', '')
        
        # Try common TLDs
        guesses = [
            f"{name}.com",
            f"{name}.net",
            f"{name}.org",
            f"{name}.io"
        ]
        
        self.logger.info(f"Guessed potential websites: {guesses}")
        return guesses[0]  # Return the first guess (.com)
'''

with open('scraper.py', 'r') as f:
    content = f.read()

# 1. Update the scrape_wikipedia method signature to accept domain parameter
content = re.sub(r'def scrape_wikipedia\(self, company_name\):', 'def scrape_wikipedia(self, company_name, domain=None):', content)

# 2. Add non-company indicators check
content = re.sub(r'is_company_article = len\(company_indicator_matches\) >= 1', 
                r'is_company_article = len(company_indicator_matches) >= 1\n                \n                # Check for common non-company indicators that might indicate we have a definition, not a company\n                non_company_indicators = ["ancient", "mythology", "historical", "history", "river", "mountain", "geographic", \n                                         "literature", "fiction", "novel", "movie", "film", "album", "song", "bible", \n                                         "greek", "roman", "definition", "idiom", "phrase", "meaning"]\n                non_company_matches = [indicator for indicator in non_company_indicators if indicator in wiki_overview]\n                \n                # If we have more non-company indicators than company indicators, this is likely not about a company\n                if len(non_company_matches) > len(company_indicator_matches):\n                    self.logger.warning(f"Wikipedia article appears to be about a non-company concept: {non_company_matches}")\n                    is_company_article = False', 
                content)

# 3. Add the guess_website_from_name method
content = content.replace('def scrape_website(self, website):', add_guess_website_method() + '\n    def scrape_website(self, website):')

# 4. Add website guessing in scrape_company
website_guess_code = '''
            # If no website is provided but we have a company name, try to guess the website
            if company_name:
                # Try to guess website from company name
                guessed_website = self.guess_website_from_name(company_name)
                if guessed_website:
                    self.logger.info(f"No website provided, guessing website: {guessed_website}")
                    result['guessed_website'] = guessed_website
                    # We'll still use this as a fallback, but note it's a guess
                    website = guessed_website
'''
content = content.replace("result['data_quality']['website_missing'] = True", "result['data_quality']['website_missing'] = True" + website_guess_code)

# 5. Update Wikipedia call to use domain
domain_code = '''
        # Try to scrape Wikipedia - but only use if relevant to the company
        # If we have a website, use it to help find the right Wikipedia page
        if company_name:
            self.logger.info(f"Scraping Wikipedia for: {company_name}")
            # Pass the website domain to help verify the right company
            domain = None
            if website:
                domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0].lower()
            wiki_data = self.scrape_wikipedia(company_name, domain)
'''
content = re.sub(r'# Try to scrape Wikipedia - but only use if relevant to the company\s+if company_name:\s+self\.logger\.info\(f"Scraping Wikipedia for: {company_name}"\)\s+wiki_data = self\.scrape_wikipedia\(company_name\)', domain_code, content)

# 6. Add domain usage in Wikipedia method
domain_usage_code = '''
            # If we have a domain, try to use it to improve search precision
            if domain:
                # Try to search for "[company_name] [domain]" to improve relevance
                search_term = f"{company_name} {domain}"
                data['source_url'] = f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}"
                self.logger.info(f"Using domain to improve search: {search_term}")
            # Add company to search terms to increase relevance
'''
content = content.replace('# Add company to search terms to increase relevance', domain_usage_code)

# 7. Add try-except to Wikipedia method
content = content.replace('def scrape_wikipedia(self, company_name, domain=None):\n        data = {', 'def scrape_wikipedia(self, company_name, domain=None):\n        data = {\n            "source_url": f"https://en.wikipedia.org/wiki/{company_name.replace(" ", "_")}"  # Store source URL\n        }\n        try:')

except_block = '''
        except Exception as e:
            self.logger.error(f"Error scraping Wikipedia for {company_name}: {e}")
        
        return data
'''
content = re.sub(r'(\s+return data\s*\n\s+def lookup_ticker_symbol)', except_block + '\n    def lookup_ticker_symbol', content)

with open('scraper.py', 'w') as f:
    f.write(content)

print("Fixed scraper.py with all improvements")