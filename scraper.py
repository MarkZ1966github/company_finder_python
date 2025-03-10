import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

class CompanyScraper:
    def __init__(self):
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
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
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
            website_data = self.scrape_website(website)
            self.update_result(result, website_data, 'Company Website')
        
        # Try to scrape Wikipedia
        wiki_data = self.scrape_wikipedia(company_name)
        self.update_result(result, wiki_data, 'Wikipedia')
        
        # Try to scrape financial data
        if company_name:
            finance_data = self.scrape_finance(company_name)
            self.update_result(result, finance_data, 'Financial Data')
        
        return result
    
    def scrape_website(self, website):
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        data = {}
        try:
            if self.driver:
                self.driver.get(website)
                time.sleep(3)  # Wait for page to load
                
                # Extract company description
                description_elements = self.driver.find_elements("xpath", 
                    "//meta[@name='description']")
                if description_elements:
                    data['description'] = description_elements[0].get_attribute('content')
                
                # Extract page content
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Try to find about section
                about_section = soup.find(lambda tag: tag.name and 
                                         any(word in tag.get_text().lower() 
                                             for word in ['about us', 'our company', 'who we are']))
                if about_section:
                    data['about'] = about_section.get_text().strip()
                
                # Try to find products/services
                products = []
                product_section = soup.find(lambda tag: tag.name and 
                                           any(word in tag.get_text().lower() 
                                               for word in ['products', 'services', 'solutions']))
                if product_section:
                    for item in product_section.find_all(['h2', 'h3', 'h4']):
                        if item.get_text().strip():
                            products.append(item.get_text().strip())
                
                if products:
                    data['products'] = products[:5]  # Limit to 5 products
        
        except Exception as e:
            print(f"Error scraping website {website}: {e}")
        
        return data
    
    def scrape_wikipedia(self, company_name):
        data = {}
        try:
            search_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Check if page exists
                if "Wikipedia does not have an article with this exact name" in soup.get_text():
                    return data
                
                # Get company overview
                first_paragraph = soup.select_one('#mw-content-text p:not(.mw-empty-elt)')
                if first_paragraph:
                    data['overview'] = first_paragraph.get_text().strip()
                
                # Get infobox data
                infobox = soup.select_one('.infobox')
                if infobox:
                    # Get founded date
                    founded = infobox.find(lambda tag: tag.name == 'th' and 'founded' in tag.get_text().lower())
                    if founded and founded.find_next('td'):
                        data['founded'] = founded.find_next('td').get_text().strip()
                    
                    # Get headquarters
                    hq = infobox.find(lambda tag: tag.name == 'th' and any(x in tag.get_text().lower() 
                                                                          for x in ['headquarters', 'location']))
                    if hq and hq.find_next('td'):
                        data['headquarters'] = hq.find_next('td').get_text().strip()
                    
                    # Get industry
                    industry = infobox.find(lambda tag: tag.name == 'th' and 'industry' in tag.get_text().lower())
                    if industry and industry.find_next('td'):
                        data['industry'] = industry.find_next('td').get_text().strip()
        
        except Exception as e:
            print(f"Error scraping Wikipedia for {company_name}: {e}")
        
        return data
    
    def scrape_finance(self, company_name):
        data = {}
        try:
            # Try Yahoo Finance
            search_url = f"https://finance.yahoo.com/quote/{company_name}"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Check if we got a valid page
                if "Symbol not found" not in self.driver.page_source:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Get stock price
                    price_element = soup.select_one('[data-test="qsp-price"]')
                    if price_element:
                        data['stock_price'] = price_element.get_text().strip()
                    
                    # Get market cap
                    market_cap = soup.find(lambda tag: tag.name == 'td' and 
                                          'Market Cap' in tag.get_text())
                    if market_cap and market_cap.find_next('td'):
                        data['market_cap'] = market_cap.find_next('td').get_text().strip()
        
        except Exception as e:
            print(f"Error scraping finance data for {company_name}: {e}")
        
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
        
        # Update company details
        for key in ['founded', 'headquarters', 'industry']:
            if key in new_data:
                result['overview'][key] = new_data[key]
                result['sources'][key] = source
        
        # Update financials
        for key in ['stock_price', 'market_cap']:
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