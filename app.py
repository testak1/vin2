import random
import time
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configuration
REQUEST_DELAY = (5, 10)  # Conservative delay between requests
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def make_request(url):
    """Make a request with random delays and headers"""
    time.sleep(random.uniform(*REQUEST_DELAY))
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.vindecoderz.com/',
        'DNT': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        return response
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")

def parse_html(html):
    """Parse the HTML content and extract vehicle information"""
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
    """Safely extract text from a BeautifulSoup selector"""
    try:
        element = soup.select_one(selector)
        if element:
            return transform(element) if transform else element.get_text(strip=True)
    except:
        pass
    return None

def scrape_vin_data(vin):
    """Scrape vehicle data from VIN decoder website"""
    start_time = time.time()
    
    try:
        url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
        response = make_request(url)
        
        if response.status_code == 200:
            result = parse_html(response.text)
            return {
                'success': True,
                'vehicle_info': result['vehicle_info'],
                'sa_codes': result['sa_codes'],
                'time': round(time.time() - start_time, 2),
                'vin': vin
            }
        else:
            return {
                'success': False,
                'error': f"HTTP Error {response.status_code}",
                'time': round(time.time() - start_time, 2),
                'vin': vin
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'time': round(time.time() - start_time, 2),
            'vin': vin
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle the main page requests"""
    result = None
    if request.method == 'POST':
        vin = request.form.get('vin', '').strip()
        if len(vin) >= 17:
            result = scrape_vin_data(vin)
    return render_template('index.html', result=result)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
