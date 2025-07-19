import random
import time
import cloudscraper
from flask import Flask, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configuration
REQUEST_DELAY = (10, 15)  # More conservative delay to avoid blocks
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def create_scraper():
    """Create a Cloudflare-aware scraper"""
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=10,
        interpreter='nodejs'
    )

def parse_html(html):
    """Parse the HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Vehicle Info
    vehicle_info = {
        'brand': safe_extract(soup, 'table.table-hover tr:nth-of-type(4) td:nth-of-type(2)'),
        'model': safe_extract(soup, 'table.table-hover tr:nth-of-type(6) td:nth-of-type(2)'),
        'year': safe_extract(soup, 'h2 strong', lambda x: x.get_text().split()[-1])
    }
    
    # SA Codes
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
    
    return {
        'vehicle_info': vehicle_info,
        'sa_codes': sa_codes
    }

def safe_extract(soup, selector, transform=None):
    """Safe element extraction"""
    try:
        element = soup.select_one(selector)
        return transform(element) if transform and element else element.get_text(strip=True) if element else None
    except:
        return None

def scrape_vin_data(vin):
    """Main scraping function"""
    start_time = time.time()
    scraper = create_scraper()
    
    try:
        time.sleep(random.uniform(*REQUEST_DELAY))
        
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.vindecoderz.com/'
        }
        
        response = scraper.get(
            f"https://www.vindecoderz.com/EN/check-lookup/{vin}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            if "Checking your browser" in response.text:
                raise Exception("Cloudflare challenge detected")
                
            result = parse_html(response.text)
            return {
                'success': True,
                'vehicle_info': result['vehicle_info'],
                'sa_codes': result['sa_codes'],
                'time': round(time.time() - start_time, 2),
                'vin': vin
            }
        else:
            raise Exception(f"HTTP Error {response.status_code}")
            
    except Exception as e:
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
