import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import logging
import os
import platform
import datetime
from GoogleNews import GoogleNews

# Import our custom ChromeDriver installer
from chromedriver_installer import setup_chrome_driver

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
        # Add additional options to improve stability
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-browser-side-navigation")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        try:
            # Check if Chrome is installed
            import os
            import platform
            import subprocess
            from shutil import which
            
            chrome_installed = False
            if platform.system() == "Darwin":  # macOS
                chrome_paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
                ]
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_installed = True
                        self.logger.info(f"Chrome found at: {path}")
                        break
            elif platform.system() == "Windows":
                chrome_paths = [
                    os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google\\Chrome\\Application\\chrome.exe'),
                    os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe')
                ]
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_installed = True
                        self.logger.info(f"Chrome found at: {path}")
                        break
            else:  # Linux and others
                chrome_installed = which('google-chrome') is not None or which('chromium-browser') is not None
                if chrome_installed:
                    self.logger.info("Chrome found in PATH")
            
            if not chrome_installed:
                self.logger.warning("Google Chrome not found on system. Browser automation will not be available.")
                self.driver = None
                return
            
            # Try multiple methods to setup ChromeDriver
            methods = [
                self._setup_with_webdriver_manager,
                self._setup_with_cached_driver,
                self._setup_with_chromedriver_binary,
                self._setup_direct_chrome
            ]
            
            for method in methods:
                try:
                    self.logger.info(f"Trying Chrome setup method: {method.__name__}")
                    success = method(chrome_options)
                    if success:
                        self.wait = WebDriverWait(self.driver, 10)  # 10 second wait
                        self.logger.info(f"Chrome driver setup successfully using {method.__name__}")
                        return
                except Exception as method_error:
                    self.logger.warning(f"{method.__name__} failed: {method_error}")
            
            # If all methods failed
            raise Exception("All ChromeDriver setup methods failed")
            
        except Exception as e:
            self.logger.error(f"Error setting up Chrome driver: {e}")
            # Fallback to requests-based scraping
            self.logger.info("Falling back to requests-based scraping without browser")
            self.driver = None
    
    def _setup_with_webdriver_manager(self, chrome_options):
        """Setup Chrome using webdriver-manager"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            # Don't specify version - let ChromeDriverManager find the compatible version
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            # Verify driver is working with a simple operation
            self.driver.get('about:blank')
            return True
        except Exception as e:
            self.logger.warning(f"ChromeDriverManager setup failed: {e}")
            return False
    
    def _setup_with_cached_driver(self, chrome_options):
        """Setup Chrome using cached driver path"""
        try:
            import os
            home_dir = os.path.expanduser("~")
            # Check multiple possible paths for cached ChromeDriver
            possible_paths = [
                os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "mac64", "latest", "chromedriver"),
                os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "mac_arm64", "latest", "chromedriver"),
                os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "mac64_m1", "latest", "chromedriver"),
                os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "win32", "latest", "chromedriver.exe"),
                os.path.join(home_dir, ".wdm", "drivers", "chromedriver", "linux64", "latest", "chromedriver")
            ]
            
            for driver_path in possible_paths:
                if os.path.exists(driver_path):
                    self.logger.info(f"Found cached ChromeDriver at: {driver_path}")
                    self.driver = webdriver.Chrome(
                        service=Service(driver_path),
                        options=chrome_options
                    )
                    return True
            
            return False
        except Exception as e:
            self.logger.warning(f"Cached driver setup failed: {e}")
            return False
    
    def _setup_with_chromedriver_binary(self, chrome_options):
        """Setup Chrome using chromedriver-binary package if installed"""
        try:
            # Try chromedriver-binary-auto first (automatically detects Chrome version)
            try:
                import chromedriver_binary_auto
                chromedriver_binary_auto.add_chromedriver_to_path()
                self.logger.info("Using chromedriver-binary-auto package")
                self.driver = webdriver.Chrome(options=chrome_options)
                return True
            except ImportError:
                self.logger.info("chromedriver-binary-auto package not installed, trying chromedriver-binary")
            
            # Fall back to regular chromedriver-binary
            import chromedriver_binary
            self.logger.info("Using chromedriver-binary package")
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except ImportError:
            self.logger.info("No chromedriver-binary packages installed")
            return False
        except Exception as e:
            self.logger.warning(f"chromedriver-binary setup failed: {e}")
            return False
    
    def _setup_direct_chrome(self, chrome_options):
        """Try direct Chrome setup as last resort"""
        try:
            self.logger.info("Attempting direct Chrome setup")
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            self.logger.warning(f"Direct Chrome setup failed: {e}")
            return False
    
    def scrape_company(self, company_name, website=None):
        result = {
            'name': company_name,
            'website': website,
            'overview': {},
            'financials': {},
            'leadership': [],
            'news': [],
            'products': [],
            'sources': {},
            'data_quality': {},
            'source_urls': {}  # Store URLs for each source to make them clickable
        }
        
        # REQUIRE website for proper company identification
        if not website:
            self.logger.warning(f"No website provided for {company_name}. Results may be less accurate.")
            result['warning'] = "No company website provided. Results may include generic information not specific to the company."
            result['data_quality']['website_missing'] = True

        # Try to scrape company website first - this is the primary source and REQUIRED for accurate data
        company_verified = False
        website_relevance_score = 0
        
        if website:
            self.logger.info(f"Scraping company website: {website}")
            website_data = self.scrape_website(website)
            self.update_result(result, website_data, 'Company Website')
            
            # Verify we have relevant company data, not generic information
            # If we have a company name, check if it appears in the website content
            if website_data and ('title' in website_data or 'description' in website_data or 'about' in website_data):
                website_content = (website_data.get('title', '') + ' ' + website_data.get('description', '') + ' ' + 
                                  website_data.get('about', '')).lower()
                
                # For debugging
                self.logger.info(f"Website content snippet: {website_content[:100]}...")
                
                # Stronger verification that this is a company website
                company_indicators = ['company', 'corporation', 'inc', 'incorporated', 'llc', 'ltd', 'limited', 
                                     'gmbh', 'ag', 'co', 'corp', 'about us', 'contact us', 'our team', 'careers',
                                     'products', 'services', 'solutions', 'customers', 'clients']
                
                # Check if this looks like a company website
                is_company_website = any(indicator in website_content for indicator in company_indicators)
                if is_company_website:
                    website_relevance_score += 2
                    self.logger.info("Website appears to be a company website (found company indicators)")
                
                # If we have a company name, check if it appears in the website content
                if company_name:
                    company_name_parts = company_name.lower().split()
                    significant_parts = [part for part in company_name_parts if len(part) > 2]
                    
                    # Check for full company name match
                    if company_name.lower() in website_content:
                        website_relevance_score += 3
                        self.logger.info(f"Full company name '{company_name}' found in website content")
                    
                    # Check for partial matches
                    company_matches = [part for part in significant_parts if part in website_content]
                    if company_matches:
                        website_relevance_score += len(company_matches)
                        self.logger.info(f"Found {len(company_matches)} company name parts in website content: {company_matches}")
                
                # Domain name match with company name
                if company_name:
                    domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0].lower()
                    if domain in company_name.lower() or any(part in domain for part in significant_parts):
                        website_relevance_score += 2
                        self.logger.info(f"Domain name '{domain}' matches company name parts")
                
                # Final relevance determination
                if website_relevance_score >= 3:
                    result['data_quality']['website_relevance'] = 'high'
                    company_verified = True
                    self.logger.info(f"Company website verified with score {website_relevance_score}")
                elif website_relevance_score > 0:
                    result['data_quality']['website_relevance'] = 'medium'
                    company_verified = True
                    self.logger.info(f"Company website partially verified with score {website_relevance_score}")
                else:
                    result['data_quality']['website_relevance'] = 'low'
                    self.logger.warning(f"Company website could not be verified (score: {website_relevance_score})")
        # Try to scrape Wikipedia - but only use if relevant to the company
        if company_name:
            self.logger.info(f"Scraping Wikipedia for: {company_name}")
            wiki_data = self.scrape_wikipedia(company_name)
            
            # Check if Wikipedia data appears to be about the company
            if wiki_data and 'overview' in wiki_data:
                wiki_overview = wiki_data['overview'].lower()
                wiki_relevance_score = 0
                
                # For debugging
                self.logger.info(f"Wikipedia overview snippet: {wiki_overview[:100]}...")
                
                # Check if this is about a company (look for company indicators)
                company_indicators = ['company', 'corporation', 'inc', 'incorporated', 'llc', 'ltd', 'limited', 'gmbh', 'ag', 'co', 'corp', 
                                     'founded', 'headquartered', 'business', 'industry', 'products', 'services']
                company_indicator_matches = [indicator for indicator in company_indicators if indicator in wiki_overview]
                is_company_article = len(company_indicator_matches) >= 1
                
                if is_company_article:
                    wiki_relevance_score += len(company_indicator_matches)
                    self.logger.info(f"Wikipedia article contains {len(company_indicator_matches)} company indicators")
                
                # Check for company name in overview
                if company_name.lower() in wiki_overview:
                    wiki_relevance_score += 3
                    self.logger.info(f"Full company name '{company_name}' found in Wikipedia overview")
                
                # Check for partial name matches
                company_name_parts = company_name.lower().split()
                significant_parts = [part for part in company_name_parts if len(part) > 2]
                company_matches = [part for part in significant_parts if part in wiki_overview]
                
                if company_matches:
                    wiki_relevance_score += len(company_matches)
                    self.logger.info(f"Found {len(company_matches)} company name parts in Wikipedia: {company_matches}")
                
                # Check for website domain match
                if website:
                    domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('.')[0].lower()
                    if domain in wiki_overview:
                        wiki_relevance_score += 2
                        self.logger.info(f"Website domain '{domain}' found in Wikipedia content")
                
                # Final relevance determination
                if wiki_relevance_score >= 4:
                    self.logger.info(f"Wikipedia data appears highly relevant to {company_name} (score: {wiki_relevance_score})")
                    self.update_result(result, wiki_data, 'Wikipedia')
                    result['data_quality']['wikipedia_relevance'] = 'high'
                elif wiki_relevance_score >= 2:
                    self.logger.info(f"Wikipedia data appears somewhat relevant to {company_name} (score: {wiki_relevance_score})")
                    self.update_result(result, wiki_data, 'Wikipedia')
                    result['data_quality']['wikipedia_relevance'] = 'medium'
                else:
                    self.logger.warning(f"Wikipedia data does not appear relevant to {company_name} as a company (score: {wiki_relevance_score})")
                    result['data_quality']['wikipedia_relevance'] = 'low'
                    # Don't update result with potentially irrelevant data
        # Try to scrape financial data - only if we have confirmed this is a company
        # Try to scrape financial data - only if we have confirmed this is a company
        if company_name and (company_verified or ('data_quality' in result and 
                                            (result['data_quality'].get('wikipedia_relevance') == 'high' or 
                                             result['data_quality'].get('wikipedia_relevance') == 'medium'))):
            self.logger.info(f"Scraping financial data for: {company_name}")
            finance_data = self.scrape_finance(company_name)
            if finance_data:
                self.update_result(result, finance_data, 'Financial Data')
                result['data_quality']['financial_data'] = 'found'
            else:
                self.logger.warning(f"No financial data found for {company_name}")
                result['data_quality']['financial_data'] = 'not_found'
        elif company_name:
            self.logger.warning(f"Skipping financial data for {company_name} as company identity could not be verified")
            result['data_quality']['finance_skipped'] = 'Company identity not verified'
        
        # Scrape news articles for the company
        if company_name:
            self.logger.info(f"Scraping news for: {company_name}")
            news_data = self.scrape_news(company_name)
            if news_data and news_data['articles']:
                # Add news articles to result
                result['news'] = news_data['articles']
                result['data_quality']['news'] = 'found'
                result['sources']['news'] = 'Google News'
                result['source_urls']['news'] = 'https://news.google.com'
            else:
                self.logger.warning(f"No news found for {company_name}")
                result['data_quality']['news'] = 'not_found'
        
        return result
    def scrape_website(self, website):
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        data = {
            'source_url': website  # Store the source URL to track where data came from
        }
        try:
            if self.driver:
                self.logger.info(f"Scraping website: {website}")
                try:
                    # Check if driver is still valid and restart if needed
                    try:
                        self.driver.current_url  # Test if session is valid
                    except Exception as session_error:
                        self.logger.warning(f"Chrome driver session invalid, restarting: {session_error}")
                        self.setup_browser()  # Recreate the browser session
                    
                    # Now try to navigate to the website
                    self.driver.get(website)
                    time.sleep(3)  # Wait for page to load
                except Exception as e:
                    self.logger.error(f"Error navigating to {website}: {e}")
                    # Fall back to requests
                    self.logger.info(f"Falling back to requests for {website}")
                    # Fall back to requests
                    self.logger.info(f"Falling back to requests for {website}")
                    try:
                        response = requests.get(website, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            # Extract title
                            if soup.title:
                                data['title'] = soup.title.text.strip()
                                self.logger.info(f"Found title via requests: {data['title']}")
                            # Extract description
                            meta_desc = soup.find('meta', attrs={'name': 'description'})
                            if meta_desc and 'content' in meta_desc.attrs:
                                data['description'] = meta_desc['content']
                                self.logger.info(f"Found description via requests: {data['description'][:50]}..." if len(data['description']) > 50 else data['description'])
                            return data
                    except Exception as req_e:
                        self.logger.error(f"Requests fallback also failed for {website}: {req_e}")
                        return data

                
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

                # Try to find leadership information
                data['leadership'] = []  # Initialize leadership array
                leadership_keywords = ['leadership', 'management', 'team', 'executives', 'founders']
                
                # Look for leadership sections
                leadership_section = soup.find(id=lambda i: i and any(keyword in i.lower() for keyword in leadership_keywords))
                if not leadership_section:
                    leadership_section = soup.find(class_=lambda c: c and any(keyword in c.lower() for keyword in leadership_keywords))
                
                if leadership_section:
                    # Try to find leadership elements - often in headings followed by descriptions
                    for name_elem in leadership_section.find_all(['h3', 'h4', 'h5', 'strong', 'b']):
                        name = name_elem.get_text().strip()
                        position_elem = name_elem.find_next(['p', 'div', 'span'])
                        position = position_elem.get_text().strip() if position_elem else 'Leadership'
                        
                        if name and len(name) < 50:  # Reasonable length for a name
                            data['leadership'].append({
                                'name': name,
                                'position': position
                            })
                            self.logger.info(f"Found leader from website: {name} ({position})")
                # Try to find leadership information
                data['leadership'] = []  # Initialize leadership array
                leadership_keywords = ['leadership', 'management', 'team', 'executives', 'founders', 'board', 'directors']
                
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
                    leaders = []
                    
                    # Look for common leadership patterns
                    # Pattern 1: h3/h4 with name followed by position in p or div
                    for name_elem in leadership_section.find_all(['h3', 'h4', 'h5', 'strong', 'b']):
                        name = name_elem.get_text().strip()
                        position_elem = name_elem.find_next(['p', 'div', 'span'])
                        position = position_elem.get_text().strip() if position_elem else 'Leadership'
                        
                        if name and len(name) < 50:  # Reasonable length for a name
                            data['leadership'].append({
                                'name': name,
                                'position': position
                            })
                            self.logger.info(f"Found leader from website: {name} ({position})")
                    
                    # If no leaders found, try other common patterns
                    if not data['leadership']:
                        # Look for list items that might contain leadership info
                        for item in leadership_section.find_all('li'):
                            text = item.get_text().strip()
                            # Try to separate name and position
                            if ',' in text or '-' in text or '–' in text:
                                parts = re.split('[,\-–]', text, 1)
                                if len(parts) >= 2:
                                    name = parts[0].strip()
                                    position = parts[1].strip()
                                    data['leadership'].append({
                                        'name': name,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader from list: {name} ({position})")
                    
                    # If still no leaders found, try looking for structured data
                    if not data['leadership']:
                        for card in leadership_section.find_all(['div', 'article', 'section']):
                            # Look for name and position within the card
                            name_elem = card.find(['h3', 'h4', 'h5', 'strong', 'b'])
                            if name_elem:
                                name = name_elem.get_text().strip()
                                position_elem = card.find(['p', 'div', 'span'])
                                position = position_elem.get_text().strip() if position_elem else 'Leadership'
                                
                                if name and len(name) < 50 and name != position:  # Avoid duplicates
                                    data['leadership'].append({
                                        'name': name,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader from card: {name} ({position})")
                # Try to find leadership information
                data['leadership'] = []  # Initialize leadership array
                leadership_keywords = ['leadership', 'management', 'team', 'executives', 'founders', 'board', 'directors']
                
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
                    leaders = []
                    
                    # Look for common leadership patterns
                    # Pattern 1: h3/h4 with name followed by position in p or div
                    for name_elem in leadership_section.find_all(['h3', 'h4', 'h5', 'strong', 'b']):
                        name = name_elem.get_text().strip()
                        position_elem = name_elem.find_next(['p', 'div', 'span'])
                        position = position_elem.get_text().strip() if position_elem else 'Leadership'
                        
                        if name and len(name) < 50:  # Reasonable length for a name
                            data['leadership'].append({
                                'name': name,
                                'position': position
                            })
                            self.logger.info(f"Found leader from website: {name} ({position})")
                    
                    # If no leaders found, try other common patterns
                    if not data['leadership']:
                        # Look for list items that might contain leadership info
                        for item in leadership_section.find_all('li'):
                            text = item.get_text().strip()
                            # Try to separate name and position
                            if ',' in text or '-' in text or '–' in text:
                                parts = re.split('[,\-–]', text, 1)
                                if len(parts) >= 2:
                                    name = parts[0].strip()
                                    position = parts[1].strip()
                                    data['leadership'].append({
                                        'name': name,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader from list: {name} ({position})")
                    
                    # If still no leaders found, try looking for structured data
                    if not data['leadership']:
                        for card in leadership_section.find_all(['div', 'article', 'section']):
                            # Look for name and position within the card
                            name_elem = card.find(['h3', 'h4', 'h5', 'strong', 'b'])
                            if name_elem:
                                name = name_elem.get_text().strip()
                                position_elem = card.find(['p', 'div', 'span'])
                                position = position_elem.get_text().strip() if position_elem else 'Leadership'
                                
                                if name and len(name) < 50 and name != position:  # Avoid duplicates
                                    data['leadership'].append({
                                        'name': name,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader from card: {name} ({position})")
                # Try to find leadership information
                data['leadership'] = []  # Initialize leadership array
                leadership_keywords = ['leadership', 'management', 'team', 'executives', 'founders', 'board', 'directors']
                
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
                    leaders = []
                    
                    # Look for common leadership patterns
                    # Pattern 1: h3/h4 with name followed by position in p or div
                    for name_elem in leadership_section.find_all(['h3', 'h4', 'h5', 'strong', 'b']):
                        name = name_elem.get_text().strip()
                        position_elem = name_elem.find_next(['p', 'div', 'span'])
                        position = position_elem.get_text().strip() if position_elem else 'Leadership'
                        
                        if name and len(name) < 50:  # Reasonable length for a name
                            data['leadership'].append({
                                'name': name,
                                'position': position
                            })
                            self.logger.info(f"Found leader from website: {name} ({position})")
                    
                    # If no leaders found, try other common patterns
                    if not data['leadership']:
                        # Look for list items that might contain leadership info
                        for item in leadership_section.find_all('li'):
                            text = item.get_text().strip()
                            # Try to separate name and position
                            if ',' in text or '-' in text or '–' in text:
                                parts = re.split('[,\-–]', text, 1)
                                if len(parts) >= 2:
                                    name = parts[0].strip()
                                    position = parts[1].strip()
                                    data['leadership'].append({
                                        'name': name,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader from list: {name} ({position})")
                    
                    # If still no leaders found, try looking for structured data
                    if not data['leadership']:
                        for card in leadership_section.find_all(['div', 'article', 'section']):
                            # Look for name and position within the card
                            name_elem = card.find(['h3', 'h4', 'h5', 'strong', 'b'])
                            if name_elem:
                                name = name_elem.get_text().strip()
                                position_elem = card.find(['p', 'div', 'span'])
                                position = position_elem.get_text().strip() if position_elem else 'Leadership'
                                
                                if name and len(name) < 50 and name != position:  # Avoid duplicates
                                    data['leadership'].append({
                                        'name': name,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader from card: {name} ({position})")
        except Exception as e:
            self.logger.error(f"Error scraping website {website}: {e}")
        
        return data
    
    def scrape_wikipedia(self, company_name):
        data = {
            'source_url': f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"  # Store source URL
        }
        try:
            # Add company to search terms to increase relevance
            if not any(term in company_name.lower() for term in ['company', 'corporation', 'inc', 'incorporated', 'llc', 'ltd', 'limited']):
                search_term = f"{company_name} company"
                data['source_url'] = f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}"
            
            # Try exact match first
            search_url = data['source_url']
            self.logger.info(f"Scraping Wikipedia: {search_url}")

            
            if self.driver:
                try:
                    # Check if driver is still valid and restart if needed
                    try:
                        self.driver.current_url  # Test if session is valid
                    except Exception as session_error:
                        self.logger.warning(f"Chrome driver session invalid, restarting: {session_error}")
                        self.setup_browser()  # Recreate the browser session
                    
                    # Now try to navigate to Wikipedia
                    self.driver.get(search_url)
                    time.sleep(2)
                except Exception as e:
                    self.logger.error(f"Error navigating to Wikipedia: {e}")
                    # Fall back to requests
                    self.logger.info(f"Falling back to requests for Wikipedia")
                    try:
                        response = requests.get(search_url, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            # Continue with normal processing using the soup object
                            # Get company overview
                            first_paragraph = soup.select_one('#mw-content-text p:not(.mw-empty-elt)')
                            if first_paragraph:
                                data['overview'] = first_paragraph.get_text().strip()
                                self.logger.info(f"Found Wikipedia overview via requests: {data['overview'][:50]}..." if len(data['overview']) > 50 else data['overview'])
                                
                                # Check if this is about a company or a generic term
                                overview_text = data['overview'].lower()
                                
                                # Check for non-company indicators
                                non_company_indicators = ['ancient', 'river', 'mythology', 'historical', 'history', 
                                                          'century', 'bc', 'b.c.', 'geographical', 'geography']
                                
                                if any(indicator in overview_text for indicator in non_company_indicators):
                                    self.logger.warning(f"Wikipedia article appears to be about a non-company entity (found non-company indicators)")
                                    data['is_company_article'] = False
                                    data['non_company_indicators'] = [ind for ind in non_company_indicators if ind in overview_text]
                                    
                                    # Try searching for the company name with "company" explicitly added
                                    company_search_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}_company"
                                    self.logger.info(f"Trying company-specific search: {company_search_url}")
                                    try:
                                        company_response = requests.get(company_search_url, timeout=10)
                                        if company_response.status_code == 200:
                                            company_soup = BeautifulSoup(company_response.text, 'html.parser')
                                            company_paragraph = company_soup.select_one('#mw-content-text p:not(.mw-empty-elt)')
                                            if company_paragraph:
                                                # Check if this looks more like a company
                                                company_indicators = ['company', 'corporation', 'founded', 'business', 'industry']
                                                company_text = company_paragraph.get_text().lower()
                                                if any(indicator in company_text for indicator in company_indicators):
                                                    data['overview'] = company_paragraph.get_text().strip()
                                                    data['is_company_article'] = True
                                                    self.logger.info(f"Found company-specific Wikipedia article")
                                    except Exception as company_search_error:
                                        self.logger.warning(f"Company-specific search failed: {company_search_error}")
                            
                            # Get infobox data
                            infobox = soup.select_one('.infobox')
                            if infobox:
                                # Process infobox data
                                self.logger.info("Found infobox via requests")
                                # Extract founded date
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
                            return data
                    except Exception as req_e:
                        self.logger.error(f"Requests fallback also failed for Wikipedia: {req_e}")
                        return data

            
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
                    
                    # Check if this is about a company or a generic term
                    overview_text = data['overview'].lower()
                    
                    # Check for non-company indicators
                    non_company_indicators = ['ancient', 'river', 'mythology', 'historical', 'history', 
                                              'century', 'bc', 'b.c.', 'geographical', 'geography']
                    
                    if any(indicator in overview_text for indicator in non_company_indicators):
                        self.logger.warning(f"Wikipedia article appears to be about a non-company entity (found non-company indicators)")
                        data['is_company_article'] = False
                        data['non_company_indicators'] = [ind for ind in non_company_indicators if ind in overview_text]
                        
                        # Try searching for the company name with "company" explicitly added
                        search_url = f"https://en.wikipedia.org/w/index.php?search={company_name.replace(' ', '+')}"
                        self.logger.info(f"Trying company-specific search: {search_url}")
                        self.driver.get(search_url)
                        time.sleep(2)
                        
                        # Check search results
                        if "Search results" not in self.driver.title:
                            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                            company_paragraph = soup.select_one('#mw-content-text p:not(.mw-empty-elt)')
                            if company_paragraph:
                                # Check if this looks more like a company
                                company_indicators = ['company', 'corporation', 'founded', 'business', 'industry']
                                company_text = company_paragraph.get_text().lower()
                                if any(indicator in company_text for indicator in company_indicators):
                                    data['overview'] = company_paragraph.get_text().strip()
                                    data['is_company_article'] = True
                                    self.logger.info(f"Found company-specific Wikipedia article")
                        else:
                            # Try to get the first search result
                            search_results = self.driver.find_elements(By.CSS_SELECTOR, '.mw-search-result-heading a')
                            if search_results:
                                first_result = search_results[0]
                                first_result.click()
                                time.sleep(2)
                                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                                company_paragraph = soup.select_one('#mw-content-text p:not(.mw-empty-elt)')
                                if company_paragraph:
                                    data['overview'] = company_paragraph.get_text().strip()
                                    data['is_company_article'] = True
                                    self.logger.info(f"Found company-specific Wikipedia article from search results")
                
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
                    
                    # Get leadership information
                    leadership_keys = ['founder', 'ceo', 'key people', 'key person', 'chairman', 'president', 'directors']
                    for key in leadership_keys:
                        leader_row = infobox.find(lambda tag: tag.name == 'th' and key in tag.get_text().lower())
                        if leader_row and leader_row.find_next('td'):
                            leader_text = leader_row.find_next('td').get_text().strip()
                            position = leader_row.get_text().strip()
                            # Split if there are multiple people
                            if ',' in leader_text or '\n' in leader_text:
                                leaders = [l.strip() for l in re.split('[,\\n]', leader_text) if l.strip()]
                                for leader in leaders:
                                    data['leadership'].append({
                                        'name': leader,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader: {leader} ({position})")
                            else:
                                data['leadership'].append({
                                    'name': leader_text,
                                    'position': position
                                })
                                self.logger.info(f"Found leader: {leader_text} ({position})")
        
        except Exception as e:
            self.logger.error(f"Error scraping Wikipedia for {company_name}: {e}")
        
        return data
    
    def lookup_ticker_symbol(self, company_name):
        """Look up the ticker symbol for a company name"""
        try:
            self.logger.info(f"Looking up ticker symbol for: {company_name}")
            
            # Check if driver is still valid and restart if needed
            if self.driver:
                try:
                    self.driver.current_url  # Test if session is valid
                except Exception as session_error:
                    self.logger.warning(f"Chrome driver session invalid, restarting: {session_error}")
                    self.setup_browser()  # Recreate the browser session
            
            # Common ticker symbols for well-known companies
            common_tickers = {
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
                'lowe\'s': 'LOW',
                'rubicon': 'RBT',
                'kore.ai': 'KORE',
                'retool': 'RTOOL',
                'asana': 'ASAN'
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
                try:
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
                except Exception as browser_error:
                    self.logger.warning(f"Browser-based ticker lookup failed: {browser_error}")
                    # Fall back to requests-based lookup
            
            # Fallback: Try using requests to get the ticker
            try:
                self.logger.info(f"Trying requests-based ticker lookup for {company_name}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                search_url = f"https://finance.yahoo.com/lookup?s={company_name.replace(' ', '+')}"
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results_table = soup.select('table[data-test="lookup-table"]')
                    
                    if results_table:
                        first_row = results_table[0].select('tbody tr')
                        if first_row:
                            symbol_cell = first_row[0].select('td')
                            if symbol_cell and len(symbol_cell) > 0:
                                symbol = symbol_cell[0].text.strip()
                                self.logger.info(f"Found ticker symbol via requests: {symbol} for {company_name}")
                                return symbol
            except Exception as req_error:
                self.logger.warning(f"Requests-based ticker lookup failed: {req_error}")
            
            # Try direct ticker lookup for common company names
            if company_lower == "microsoft":
                return "MSFT"
            elif company_lower == "apple":
                return "AAPL"
            elif company_lower == "rubicon":
                return "RBT"
            elif company_lower == "asana":
                return "ASAN"
            elif company_lower == "retool":
                return "RTOOL"
            
            # Generate a fake ticker based on company name for private companies
            if company_name:
                # Use first letters of each word in the company name
                words = company_name.split()
                if len(words) > 1:
                    ticker = ''.join(word[0].upper() for word in words if word)
                    if len(ticker) >= 2:
                        self.logger.info(f"Generated ticker symbol from name: {ticker} for {company_name}")
                        return ticker
                else:
                    # If single word, use first 4 letters or whole word if shorter
                    ticker = company_name[:4].upper()
                    self.logger.info(f"Generated ticker symbol from name: {ticker} for {company_name}")
                    return ticker
            
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
            
            # Try multiple finance sources
            # 1. Alpha Vantage API (free tier)
            alpha_vantage_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey=demo"
            self.logger.info(f"Trying Alpha Vantage API for {ticker}")
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(alpha_vantage_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    av_data = response.json()
                    if 'Global Quote' in av_data and av_data['Global Quote']:
                        quote = av_data['Global Quote']
                        if '05. price' in quote:
                            data['stock_price'] = quote['05. price']
                            self.logger.info(f"Found stock price via Alpha Vantage: {data['stock_price']}")
                        if '08. previous close' in quote:
                            data['previous_close'] = quote['08. previous close']
                        if '09. change' in quote:
                            data['change'] = quote['09. change']
                        if '10. change percent' in quote:
                            data['change_percent'] = quote['10. change percent']
                        # If we got data, return it without trying other sources
                        if 'stock_price' in data:
                            return data
            except Exception as av_error:
                self.logger.warning(f"Alpha Vantage API failed: {av_error}")
            
            # 2. Try Yahoo Finance with the ticker as fallback
            search_url = f"https://finance.yahoo.com/quote/{ticker}"
            self.logger.info(f"Scraping financial data from: {search_url}")
            if self.driver:
                try:
                    self.driver.get(search_url)
                    time.sleep(3)
                except Exception as e:
                    self.logger.error(f"Error navigating to Yahoo Finance: {e}")
                    # Fall back to requests
                    self.logger.info(f"Falling back to requests for Yahoo Finance")
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        response = requests.get(search_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Check if we got a valid page
                            if "Symbol not found" not in response.text:
                                # Get stock price
                                try:
                                    price_element = soup.select_one('[data-field="regularMarketPrice"]')
                                    if price_element:
                                        price_text = price_element.get_text().strip()
                                        # Validate price data - should be a reasonable number
                                        # Check if it's a valid price (not some error value like 5,630)
                                        try:
                                            # Remove commas and convert to float for validation
                                            price_value = float(price_text.replace(',', ''))
                                            if price_value > 0 and price_value < 100000:  # Reasonable price range
                                                data['stock_price'] = price_text
                                                self.logger.info(f"Found stock price via requests: {data['stock_price']}")
                                            else:
                                                self.logger.warning(f"Stock price out of reasonable range: {price_value}")
                                        except ValueError:
                                            self.logger.warning(f"Invalid price format: {price_text}")
                                except Exception as price_e:
                                    self.logger.warning(f"Error getting stock price via requests: {price_e}")
                                
                                # Get market cap
                                try:
                                    market_cap = soup.find('td', string=lambda text: text and 'Market Cap' in text)
                                    if market_cap and market_cap.find_next('td'):
                                        data['market_cap'] = market_cap.find_next('td').get_text().strip()
                                        self.logger.info(f"Found market cap via requests: {data['market_cap']}")
                                except Exception as mc_e:
                                    self.logger.warning(f"Error getting market cap via requests: {mc_e}")
                                
                                # Get P/E Ratio
                                try:
                                    pe_ratio = soup.find('td', string=lambda text: text and 'PE Ratio' in text)
                                    if pe_ratio and pe_ratio.find_next('td'):
                                        data['pe_ratio'] = pe_ratio.find_next('td').get_text().strip()
                                        self.logger.info(f"Found P/E ratio via requests: {data['pe_ratio']}")
                                except Exception as pe_e:
                                    self.logger.warning(f"Error getting P/E ratio via requests: {pe_e}")
                            else:
                                self.logger.warning(f"Symbol not found for ticker via requests: {ticker}")
                            return data
                    except Exception as req_e:
                        self.logger.error(f"Requests fallback also failed for Yahoo Finance: {req_e}")
                        return data


                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Get stock price
                    try:
                        price_element = soup.select_one('[data-field="regularMarketPrice"]')
                        if price_element:
                            data['stock_price'] = price_element.get_text().strip()
                            self.logger.info(f"Found stock price: {data['stock_price']}")
                    except Exception as e:
                        self.logger.warning(f"Error getting stock price: {e}")
                        
                        # Get leadership information
                        leadership_keys = ['founder', 'ceo', 'key people', 'key person', 'chairman', 'president', 'directors']
                        for key in leadership_keys:
                            leader_row = infobox.find(lambda tag: tag.name == 'th' and key in tag.get_text().lower())
                            if leader_row and leader_row.find_next('td'):
                                leader_text = leader_row.find_next('td').get_text().strip()
                                position = leader_row.get_text().strip()
                                # Split if there are multiple people
                                if ',' in leader_text or '\n' in leader_text:
                                    leaders = [l.strip() for l in re.split('[,\\n]', leader_text) if l.strip()]
                                    for leader in leaders:
                                        data['leadership'].append({
                                            'name': leader,
                                            'position': position
                                        })
                                        self.logger.info(f"Found leader: {leader} ({position})")
                                else:
                                    data['leadership'].append({
                                        'name': leader_text,
                                        'position': position
                                    })
                                    self.logger.info(f"Found leader: {leader_text} ({position})")
                    
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
        
        # Update leadership information
        if 'leadership' in new_data and new_data['leadership']:
            for leader in new_data['leadership']:
                leader_copy = leader.copy()  # Create a copy to avoid modifying the original
                leader_copy['source'] = source  # Add source information
                result['leadership'].append(leader_copy)
                self.logger.info(f"Added leadership information: {leader['name']}")
        
        # Update leadership information
        if 'leadership' in new_data and new_data['leadership']:
            for leader in new_data['leadership']:
                leader_copy = leader.copy()  # Create a copy to avoid modifying the original
                leader_copy['source'] = source  # Add source information
                result['leadership'].append(leader_copy)
                self.logger.info(f"Added leadership information: {leader['name']}")
        
        # Update products
        if 'products' in new_data and new_data['products']:
            for product in new_data['products']:
                result['products'].append({
                    'name': product,
                    'source': source
                })

        # Store source URLs
        if 'source_url' in new_data:
            source_key = source.lower().replace(' ', '_')
            result['source_urls'][source_key] = new_data['source_url']
    def scrape_news(self, company_name):
        """Scrape news articles for a company using GoogleNews"""
        self.logger.info(f"Fetching news articles for: {company_name}")
        data = {
            'articles': [],
            'source_url': f"https://news.google.com/search?q={company_name.replace(' ', '+')}"
        }
        
        try:
            # Initialize GoogleNews
            googlenews = GoogleNews(lang='en', period='7d')
            googlenews.search(company_name)
            
            # Handle potential None result from GoogleNews
            try:
                news_results = googlenews.results()
                if news_results is None:
                    news_results = []
                    self.logger.warning("GoogleNews returned None results")
            except Exception as results_error:
                self.logger.warning(f"Error getting GoogleNews results: {results_error}")
                news_results = []
            # Log the number of results found
            if news_results:
                self.logger.info(f"Found {len(news_results)} news articles for {company_name}")
            else:
                self.logger.warning(f"No news articles found for {company_name}")
                return data
            
            # Process up to 5 articles
            for i, article in enumerate(news_results[:5]):
                try:
                    # Extract article information
                    title = article.get('title', 'No title available')
                    link = article.get('link', '')
                    published_date = article.get('date', '')
                    source = article.get('media', 'Unknown Source')
                    description = article.get('desc', 'No description available')
                    
                    # Format the date if available
                    formatted_date = published_date
                    if published_date:
                        try:
                            if isinstance(published_date, datetime.datetime):
                                formatted_date = published_date.strftime('%Y-%m-%d')
                        except Exception as date_error:
                            self.logger.warning(f"Error formatting date: {date_error}")
                    
                    # Add article to results
                    data['articles'].append({
                        'title': title,
                        'link': link,
                        'date': formatted_date,
                        'source': source,
                        'description': description
                    })
                    self.logger.info(f"Added news article: {title}")
                    
                except Exception as article_error:
                    self.logger.error(f"Error processing article {i}: {article_error}")
                    continue
            
            # If GoogleNews fails, try a fallback method
            if not data['articles']:
                self.logger.warning("GoogleNews returned no articles, trying fallback method")
                # Use requests to get news from a different source
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
                                self.logger.info(f"Added news article from fallback: {title}")
                            except Exception as card_error:
                                self.logger.error(f"Error processing fallback article {i}: {card_error}")
                                continue
                except Exception as fallback_error:
                    self.logger.error(f"Fallback news method failed: {fallback_error}")
            
        except Exception as e:
            self.logger.error(f"Error scraping news for {company_name}: {e}")
        
        return data

    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()