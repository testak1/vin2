import random
import time
from flask import Flask, render_template, request
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configuration
REQUEST_DELAY = (1, 3)  # Random delay between 1-3 seconds
MAX_RETRIES = 2
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.vindecoderz.com/',
        'DNT': '1'
    }

def scrape_vin_data(vin):
    scraper = cloudscraper.create_scraper(
        interpreter='nodejs',
        delay=10,
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(random.uniform(*REQUEST_DELAY))
            
            start_time = time.time()
            response = scraper.get(
                url, 
                headers=get_random_headers(), 
                timeout=30
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                if "Checking your browser" in response.text:
                    raise Exception("Cloudflare challenge detected")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Vehicle Info
                vehicle_info = {
                    'brand': soup.select_one('table.table-hover tr:nth-of-type(4) td:nth-of-type(2)').get_text(strip=True),
                    'model': soup.select_one('table.table-hover tr:nth-of-type(6) td:nth-of-type(2)').get_text(strip=True),
                    'year': soup.select_one('h2 strong').get_text().split()[-1] if soup.select_one('h2 strong') else None
                }
                
                # SA Codes
                sa_codes = []
                for row in soup.select('div.section table.table-striped:nth-of-type(2) tbody tr'):
                    cells = row.select('td')
                    if len(cells) >= 2:
                        sa_codes.append({
                            'code': cells[0].get_text(strip=True),
                            'description': cells[1].get_text(strip=True)
                        })
                
                return {
                    'success': True,
                    'vehicle_info': vehicle_info,
                    'sa_codes': sa_codes,
                    'time': round(elapsed_time, 2),
                    'vin': vin
                }
                
            elif response.status_code == 403:
                if attempt < MAX_RETRIES - 1:
                    continue
                return {
                    'success': False,
                    'error': "Access denied. The website blocked our request.",
                    'time': round(elapsed_time, 2),
                    'vin': vin
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'time': round(elapsed_time, 2) if 'elapsed_time' in locals() else 0,
                'vin': vin
            }

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        vin = request.form.get('vin', '').strip()
        if len(vin) >= 17:
            result = scrape_vin_data(vin)
    return render_template('index.html', result=result)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
