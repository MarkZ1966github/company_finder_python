#!/usr/bin/env python3
import re

# Read the file
with open('scraper.py', 'r') as file:
    content = file.read()

# Fix the news scraping function to handle None results better
news_fix = '''
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
            news_results = []
            try:
                results = googlenews.results()
                # Ensure we have a valid list
                if results is not None and isinstance(results, list):
                    news_results = results
                else:
                    self.logger.warning(f"GoogleNews returned invalid results for {company_name}")
            except Exception as results_error:
                self.logger.warning(f"Error getting GoogleNews results: {results_error}")
            
            # Log the number of results found
            if news_results:
                self.logger.info(f"Found {len(news_results)} news articles for {company_name}")
            else:
                self.logger.warning(f"No news articles found for {company_name}")
                # Try fallback immediately
                return self._try_news_fallback(company_name, data)
            
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
            
            # If GoogleNews fails or returns no articles, try a fallback method
            if not data['articles']:
                return self._try_news_fallback(company_name, data)
            
        except Exception as e:
            self.logger.error(f"Error scraping news for {company_name}: {e}")
            # Try fallback on any exception
            return self._try_news_fallback(company_name, data)
        
        return data
    
    def _try_news_fallback(self, company_name, data):
        """Fallback method for news when GoogleNews fails"""
        self.logger.warning(f"Trying fallback news method for {company_name}")
        
        # Try Bing News
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
            
            # Try one more fallback - direct search
            try:
                search_url = f"https://www.google.com/search?q={company_name}+news&tbm=nws"
                response = requests.get(search_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    news_divs = soup.select('div.SoaBEf')
                    for i, div in enumerate(news_divs[:5]):
                        try:
                            title_elem = div.select_one('div.mCBkyc')
                            link_elem = div.select_one('a')
                            source_elem = div.select_one('.CEMjEf')
                            description_elem = div.select_one('.GI74Re')
                            
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
        
        return data
'''

# Find the old scrape_news method and replace it
pattern = r"def scrape_news\(self, company_name\):.*?return data"
replacement = news_fix

# Apply replacements
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the file back
with open('scraper.py', 'w') as file:
    file.write(content)

print("News scraping has been improved in scraper.py.")