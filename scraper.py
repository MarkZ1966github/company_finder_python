import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class CompanyScraper:
    def __init__(self):
        # Setup logger
        self.logger = logging.getLogger('CompanyScraper')
        # Setup headless browser
        self.setup_browser()
    
    def setup_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, 10)  # 10 second wait
            self.logger.info("Chrome driver setup successfully")
        except Exception as e:
            self.logger.error(f"Error setting up Chrome driver: {e}")
            self.driver = None
    
    def scrape_company(self, company_name, website=None):
        result = {
            'name': company_name,
            'website': website,
            'overview': {},
            'financials': {},
            'leadership': [],
            'news': [],
            'products': [],
            'sources': {}
        }
        
        # Try to scrape company website
        if website:
            self.logger.info(f"Scraping company website: {website}")
            website_data = self.scrape_website(website)
            self.update_result(result, website_data, 'Company Website')
        
        # Try to scrape Wikipedia
        self.logger.info(f"Scraping Wikipedia for: {company_name}")
        wiki_data = self.scrape_wikipedia(company_name)
        self.update_result(result, wiki_data, 'Wikipedia')
        
        # Try to scrape financial data
        if company_name:
            self.logger.info(f"Scraping financial data for: {company_name}")
            finance_data = self.scrape_finance(company_name)
            self.update_result(result, finance_data, 'Financial Data')
        
        return result
    
    def scrape_website(self, website):
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        data = {}
        try:
            if self.driver:
                self.logger.info(f"Scraping website: {website}")
                self.driver.get(website)
                time.sleep(3)  # Wait for page to load
                
                # Extract company description
                description_elements = self.driver.find_elements(By.XPATH, 
                    "//meta[@name='description']")
                if description_elements:
                    data['description'] = description_elements[0].get_attribute('content')
                    self.logger.info(f"Found description: {data['description'][:50]}..." if 'description' in data and len(data['description']) > 50 else "No description found")
                
                # Try to extract title
                title = self.driver.title
                if title:
                    data['title'] = title
                    self.logger.info(f"Found title: {title}")
                
                # Extract page content
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Try to find about section - more comprehensive search
                about_keywords = ['about us', 'our company', 'who we are', 'about', 'mission', 'vision']
                
                # Check for about sections by ID or class
                about_section = soup.find(id=lambda i: i and any(keyword in i.lower() for keyword in about_keywords))
                if not about_section:
                    about_section = soup.find(class_=lambda c: c and any(keyword in c.lower() for keyword in about_keywords))
                
                # Check for about sections by content
                if not about_section:
                    about_section = soup.find(lambda tag: tag.name and 
                                             any(word in tag.get_text().lower() 
                                                 for word in about_keywords))
                
                if about_section:
                    data['about'] = about_section.get_text().strip()
                    self.logger.info(f"Found about section: {data['about'][:50]}..." if len(data['about']) > 50 else data['about'])
                
                # Try to find products/services - more comprehensive search
                products = []
                product_keywords = ['products', 'services', 'solutions', 'offerings', 'what we do']
                
                # Try by ID or class first
                product_section = soup.find(id=lambda i: i and any(keyword in i.lower() for keyword in product_keywords))
                if not product_section:
                    product_section = soup.find(class_=lambda c: c and any(keyword in c.lower() for keyword in product_keywords))
                
                # Try by content
                if not product_section:
                    product_section = soup.find(lambda tag: tag.name and 
                                               any(word in tag.get_text().lower() 
                                                   for word in product_keywords))
                
                if product_section:
                    # Look for headings first
                    for item in product_section.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
                        if item.get_text().strip() and len(item.get_text().strip()) < 100:  # Reasonable length for a product name
                            products.append(item.get_text().strip())
                    
                    # If no headings found, try list items
                    if not products:
                        for item in product_section.find_all(['li']):
                            if item.get_text().strip() and len(item.get_text().strip()) < 100:
                                products.append(item.get_text().strip())
                
                if products:
                    data['products'] = products[:5]  # Limit to 5 products
                    self.logger.info(f"Found {len(products)} products/services")
        
        except Exception as e:
            self.logger.error(f"Error scraping website {website}: {e}")
        
        return data
    
    def scrape_wikipedia(self, company_name):
        data = {}
        try:
            # Try exact match first
            search_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
            self.logger.info(f"Scraping Wikipedia: {search_url}")
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Check if page exists
                if "Wikipedia does not have an article with this exact name" in soup.get_text():
                    # Try search instead
                    self.logger.info(f"No exact match for {company_name}, trying search")
                    search_url = f"https://en.wikipedia.org/w/index.php?search={company_name.replace(' ', '+')}"
                    self.driver.get(search_url)
                    time.sleep(2)
                    
                    # Check if we were redirected to a page (means there was a close match)
                    if "Search results" not in self.driver.title:
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    else:
                        # Try to get the first search result
                        search_results = self.driver.find_elements(By.CSS_SELECTOR, '.mw-search-result-heading a')
                        if search_results:
                            first_result = search_results[0]
                            first_result.click()
                            time.sleep(2)
                            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        else:
                            self.logger.warning(f"No Wikipedia results found for {company_name}")
                            return data
                
                # Get company overview
                first_paragraph = soup.select_one('#mw-content-text p:not(.mw-empty-elt)')
                if first_paragraph:
                    data['overview'] = first_paragraph.get_text().strip()
                    self.logger.info(f"Found Wikipedia overview: {data['overview'][:50]}..." if len(data['overview']) > 50 else data['overview'])
                
                # Get infobox data
                infobox = soup.select_one('.infobox')
                if infobox:
                    # Get founded date
                    founded = infobox.find(lambda tag: tag.name == 'th' and 'founded' in tag.get_text().lower())
                    if founded and founded.find_next('td'):
                        data['founded'] = founded.find_next('td').get_text().strip()
                        self.logger.info(f"Found founding date: {data['founded']}")
                    
                    # Get headquarters
                    hq = infobox.find(lambda tag: tag.name == 'th' and any(x in tag.get_text().lower() 
                                                                          for x in ['headquarters', 'location']))
                    if hq and hq.find_next('td'):
                        data['headquarters'] = hq.find_next('td').get_text().strip()
                        self.logger.info(f"Found headquarters: {data['headquarters']}")
                    
                    # Get industry
                    industry = infobox.find(lambda tag: tag.name == 'th' and 'industry' in tag.get_text().lower())
                    if industry and industry.find_next('td'):
                        data['industry'] = industry.find_next('td').get_text().strip()
                        self.logger.info(f"Found industry: {data['industry']}")
                    
                    # Get number of employees
                    employees = infobox.find(lambda tag: tag.name == 'th' and 'employees' in tag.get_text().lower())
                    if employees and employees.find_next('td'):
                        data['employees'] = employees.find_next('td').get_text().strip()
                        self.logger.info(f"Found employee count: {data['employees']}")
                    
                    # Get revenue
                    revenue = infobox.find(lambda tag: tag.name == 'th' and 'revenue' in tag.get_text().lower())
                    if revenue and revenue.find_next('td'):
                        data['revenue'] = revenue.find_next('td').get_text().strip()
                        self.logger.info(f"Found revenue: {data['revenue']}")
        
        except Exception as e:
            self.logger.error(f"Error scraping Wikipedia for {company_name}: {e}")
        
        return data
    
    def lookup_ticker_symbol(self, company_name):
        """Look up the ticker symbol for a company name"""
        try:
            self.logger.info(f"Looking up ticker symbol for: {company_name}")
            
            # Common ticker symbols for well-known companies
            common_tickers = {
                'apple': 'AAPL',
                'microsoft': 'MSFT',
                'amazon': 'AMZN',
                'google': 'GOOGL',
                'alphabet': 'GOOGL',
                'meta': 'META',
                'facebook': 'META',
                'netflix': 'NFLX',
                'tesla': 'TSLA',
                'nvidia': 'NVDA',
                'ibm': 'IBM',
                'intel': 'INTC',
                'adobe': 'ADBE',
                'oracle': 'ORCL',
                'salesforce': 'CRM',
                'cisco': 'CSCO',
                'walmart': 'WMT',
                'disney': 'DIS',
                'coca-cola': 'KO',
                'coke': 'KO',
                'pepsi': 'PEP',
                'pepsico': 'PEP',
                'mcdonald\'s': 'MCD',
                'mcdonalds': 'MCD',
                'starbucks': 'SBUX',
                'nike': 'NKE',
                'boeing': 'BA',
                'ford': 'F',
                'general motors': 'GM',
                'gm': 'GM',
                'exxon': 'XOM',
                'exxonmobil': 'XOM',
                'chevron': 'CVX',
                'jpmorgan': 'JPM',
                'jp morgan': 'JPM',
                'bank of america': 'BAC',
                'wells fargo': 'WFC',
                'goldman sachs': 'GS',
                'morgan stanley': 'MS',
                'visa': 'V',
                'mastercard': 'MA',
                'american express': 'AXP',
                'amex': 'AXP',
                'paypal': 'PYPL',
                'at&t': 'T',
                'verizon': 'VZ',
                'comcast': 'CMCSA',
                'johnson & johnson': 'JNJ',
                'pfizer': 'PFE',
                'merck': 'MRK',
                'ups': 'UPS',
                'fedex': 'FDX',
                'target': 'TGT',
                'home depot': 'HD',
                'lowes': 'LOW',
                'lowe\'s': 'LOW'
            }
            
            # Check if we have a known ticker for this company
            company_lower = company_name.lower()
            if company_lower in common_tickers:
                ticker = common_tickers[company_lower]
                self.logger.info(f"Found ticker symbol in common tickers: {ticker} for {company_name}")
                return ticker
                
            # Try Yahoo Finance search
            search_url = f"https://finance.yahoo.com/lookup?s={company_name.replace(' ', '+')}"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(2)
                
                # Check if search results exist
                results_table = self.driver.find_elements(By.CSS_SELECTOR, 'table[data-test="lookup-table"]')
                if results_table:
                    # Find the first row in the results table
                    first_row = self.driver.find_elements(By.CSS_SELECTOR, 'table[data-test="lookup-table"] tbody tr')
                    if first_row:
                        # Get the symbol from the first column
                        symbol_element = first_row[0].find_elements(By.TAG_NAME, 'td')
                        if symbol_element and len(symbol_element) > 0:
                            symbol = symbol_element[0].text.strip()
                            self.logger.info(f"Found ticker symbol: {symbol} for {company_name}")
                            return symbol
            
            # Try direct ticker lookup for common company names
            if company_lower == "microsoft":
                return "MSFT"
            elif company_lower == "apple":
                return "AAPL"
            
            self.logger.warning(f"No ticker symbol found for: {company_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error looking up ticker symbol for {company_name}: {e}")
            return None
    def scrape_finance(self, company_name):
        data = {}
        try:
            # First try to find the ticker symbol
            ticker = self.lookup_ticker_symbol(company_name)
            
            if not ticker:
                self.logger.warning(f"No ticker found for {company_name}, using company name as ticker")
                ticker = company_name
            
            # Try Yahoo Finance with the ticker
            search_url = f"https://finance.yahoo.com/quote/{ticker}"
            self.logger.info(f"Scraping financial data from: {search_url}")
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Check if we got a valid page
                if "Symbol not found" not in self.driver.page_source:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Get stock price
                    try:
                        price_element = soup.select_one('[data-field="regularMarketPrice"]')
                        if price_element:
                            data['stock_price'] = price_element.get_text().strip()
                            self.logger.info(f"Found stock price: {data['stock_price']}")
                    except Exception as e:
                        self.logger.warning(f"Error getting stock price: {e}")
                    
                    # Get market cap
                    try:
                        market_cap = soup.find('td', string=lambda text: text and 'Market Cap' in text)
                        if market_cap and market_cap.find_next('td'):
                            data['market_cap'] = market_cap.find_next('td').get_text().strip()
                            self.logger.info(f"Found market cap: {data['market_cap']}")
                    except Exception as e:
                        self.logger.warning(f"Error getting market cap: {e}")
                    
                    # Get additional financial info
                    try:
                        # P/E Ratio
                        pe_ratio = soup.find('td', string=lambda text: text and 'PE Ratio' in text)
                        if pe_ratio and pe_ratio.find_next('td'):
                            data['pe_ratio'] = pe_ratio.find_next('td').get_text().strip()
                            self.logger.info(f"Found P/E ratio: {data['pe_ratio']}")
                    except Exception as e:
                        self.logger.warning(f"Error getting P/E ratio: {e}")
                else:
                    self.logger.warning(f"Symbol not found for ticker: {ticker}")
        
        except Exception as e:
            self.logger.error(f"Error scraping finance data for {company_name}: {e}")
        
        return data
    
    def update_result(self, result, new_data, source):
        if not new_data:
            return
        
        # Update overview
        if 'overview' in new_data:
            result['overview']['description'] = new_data['overview']
            result['sources']['overview'] = source
        
        if 'description' in new_data:
            result['overview']['summary'] = new_data['description']
            result['sources']['summary'] = source
        
        if 'about' in new_data:
            result['overview']['about'] = new_data['about']
            result['sources']['about'] = source
            
        if 'title' in new_data:
            result['overview']['title'] = new_data['title']
            result['sources']['title'] = source
        
        # Update company details
        for key in ['founded', 'headquarters', 'industry', 'employees', 'revenue']:
            if key in new_data:
                result['overview'][key] = new_data[key]
                result['sources'][key] = source
        
        # Update financials
        for key in ['stock_price', 'market_cap', 'pe_ratio']:
            if key in new_data:
                result['financials'][key] = new_data[key]
                result['sources'][key] = source
        
        # Update products
        if 'products' in new_data and new_data['products']:
            for product in new_data['products']:
                result['products'].append({
                    'name': product,
                    'source': source
                })
    
    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()