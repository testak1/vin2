import random
import time
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configuration
REQUEST_DELAY = (15, 30)  # Very conservative delay (15-30 seconds)
MAX_RETRIES = 2
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_headers():
    """Generate random headers for each request"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
    }

def parse_html(html):
    """Parse HTML response"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Error if CAPTCHA page detected
    if "captcha" in html.lower() or "cloudflare" in html.lower():
        raise Exception("CAPTCHA challenge detected")
    
    # Extract vehicle data
    vehicle_info = {
        'brand': safe_extract(soup, 'table.table-hover tr:nth-of-type(4) td:nth-of-type(2)'),
        'model': safe_extract(soup, 'table.table-hover tr:nth-of-type(6) td:nth-of-type(2)'),
        'year': safe_extract(soup, 'h2 strong', lambda x: x.get_text().split()[-1])
    }
    
    # Extract SA codes
    sa_codes = []
    sa_table = soup.select('div.section table.table-striped')
    if len(sa_table) > 1:
        for row in sa_table[1].select('tbody tr'):
            cells = row.select('td')
            if len(cells) >= 2:
                sa_codes.append({
                    'code': cells[0].get_text(strip=True),
                    'description': cells[1].get_text(strip=True)
                })
    
    return {'vehicle_info': vehicle_info, 'sa_codes': sa_codes}

def safe_extract(soup, selector, transform=None):
    """Safe HTML element extraction"""
    try:
        element = soup.select_one(selector)
        return transform(element) if transform and element else element.get_text(strip=True) if element else None
    except:
        return None

def scrape_vin_data(vin):
    """Main scraping function with retry logic"""
    start_time = time.time()
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(random.uniform(*REQUEST_DELAY))
            
            session = requests.Session()
            response = session.get(
                f"https://www.vindecoderz.com/EN/check-lookup/{vin}",
                headers=get_headers(),
                timeout=30
            )
            
            if response.status_code == 403:
                raise Exception("Cloudflare block (403 Forbidden)")
            
            result = parse_html(response.text)
            return {
                'success': True,
                'data': result,
                'time': round(time.time() - start_time, 2),
                'vin': vin
            }
            
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return {
                    'success': False,
                    'error': str(e),
                    'time': round(time.time() - start_time, 2),
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
