from scraper import CompanyScraper
import json
import sys

def test_scraper(company_name, website=None):
    print(f"Testing scraper with company: {company_name}, website: {website}")
    
    scraper = CompanyScraper()
    result = scraper.scrape_company(company_name, website)
    
    # Pretty print the result
    print(json.dumps(result, indent=2))
    
    # Check if we got proper data
    if result.get('overview') and (result['overview'].get('description') or result['overview'].get('summary')):
        print(f"\nSUCCESS: Retrieved company description")
        
        # Print the description
        description = result['overview'].get('description') or result['overview'].get('summary')
        print(f"Description: {description[:200]}..." if len(description) > 200 else f"Description: {description}")
    else:
        print("\nFAILURE: No company description found")
        
    if result.get('products') and len(result['products']) > 0:
        print(f"\nSUCCESS: Found {len(result['products'])} products")
        # Print the first 3 products
        for i, product in enumerate(result['products'][:3]):
            print(f"Product {i+1}: {product['name']} (Source: {product['source']})")
    else:
        print("\nFAILURE: No products found")
        
    if result.get('news') and len(result['news']) > 0:
        print(f"\nSUCCESS: Found {len(result['news'])} news articles")
        # Print the first 3 news articles
        for i, article in enumerate(result['news'][:3]):
            print(f"Article {i+1}: {article['title']}")
            print(f"  Source: {article['source']}, Date: {article['date']}")
    else:
        print("\nFAILURE: No news found")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
        website = sys.argv[2] if len(sys.argv) > 2 else None
        test_scraper(company_name, website)
    else:
        # Run tests with a few example companies
        test_companies = [
            ("Rubicon", "rubicon.com"),
            ("Microsoft", "microsoft.com"),
            ("Asana", "asana.com"),
            ("Retool", "retool.com")
        ]
        
        print("Running tests with example companies...\n")
        for name, site in test_companies:
            print(f"\n{'='*50}")
            print(f"Testing {name} ({site})")
            print(f"{'='*50}\n")
            test_scraper(name, site)
            print("\n")
        
        print("All tests completed!")