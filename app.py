from flask import Flask, render_template, request, jsonify
from scraper import CompanyScraper
import os

app = Flask(__name__)
scraper = CompanyScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_company():
    data = request.json
    company_name = data.get('name', '')
    website = data.get('website', '')
    
    if not company_name and not website:
        return jsonify({'error': 'Company name or website required'}), 400
    
    try:
        result = scraper.scrape_company(company_name, website)
        return jsonify(result)
    except Exception as e:
        print(f"Error scraping company: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)