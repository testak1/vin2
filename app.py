import random
import time
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# Configuration
REQUEST_DELAY = (3, 7)  # Polite delay between requests
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def get_chrome_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Vehicle Info
    vehicle_info = {
        'brand': soup.select_one('table.table-hover tr:nth-of-type(4) td:nth-of-type(2)').get_text(strip=True),
        'model': soup.select_one('table.table-hover tr:nth-of-type(6) td:nth-of-type(2)').get_text(strip=True),
        'year': soup.select_one('h2 strong').get_text().split()[-1] if soup.select_one('h2 strong') else None
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

def scrape_vin_data(vin):
    start_time = time.time()
    result = None
    
    # Be polite with delays
    time.sleep(random.uniform(*REQUEST_DELAY))
    
    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(f"https://www.vindecoderz.com/EN/check-lookup/{vin}")
        
        # Wait for page to load
        time.sleep(5)
        
        # Check for Cloudflare challenge
        if "Checking your browser" in driver.page_source:
            # If challenge detected, wait longer
            time.sleep(10)
        
        html = driver.page_source
        result = parse_html(html)
        
    except Exception as e:
        print(f"Scraping error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'time': round(time.time() - start_time, 2),
            'vin': vin
        }
    finally:
        if driver:
            driver.quit()
    
    elapsed_time = time.time() - start_time
    
    if result:
        return {
            'success': True,
            'vehicle_info': result['vehicle_info'],
            'sa_codes': result['sa_codes'],
            'time': round(elapsed_time, 2),
            'vin': vin
        }
    else:
        return {
            'success': False,
            'error': "Failed to retrieve data. Website protections may be blocking us.",
            'time': round(elapsed_time, 2),
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
