import random
import time
from flask import Flask, render_template, request
import cloudscraper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# Configuration
REQUEST_DELAY = (3, 7)  # More polite delay range
MAX_RETRIES = 2
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.vindecoderz.com/',
        'DNT': '1',
        'Accept': 'text/html,application/xhtml+xml'
    }

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

def scrape_with_cloudscraper(vin):
    scraper = cloudscraper.create_scraper(
        interpreter='nodejs',
        delay=10,
        browser={
            'browser': 'firefox',
            'platform': 'linux',
            'desktop': True
        }
    )
    
    try:
        response = scraper.get(
            f"https://www.vindecoderz.com/EN/check-lookup/{vin}",
            headers=get_random_headers(),
            timeout=30
        )
        return response.text if response.status_code == 200 else None
    except:
        return None

def scrape_with_selenium(vin):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.get(f"https://www.vindecoderz.com/EN/check-lookup/{vin}")
        time.sleep(5)  # Allow page to load
        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        print(f"Selenium error: {str(e)}")
        return None

def scrape_vin_data(vin):
    start_time = time.time()
    result = None
    method_used = None
    
    # Be polite with delays
    time.sleep(random.uniform(*REQUEST_DELAY))
    
    # First try Cloudscraper
    html = scrape_with_cloudscraper(vin)
    if html:
        try:
            result = parse_html(html)
            method_used = 'cloudscraper'
        except Exception as e:
            print(f"Cloudscraper parse error: {str(e)}")
    
    # If Cloudscraper fails, try Selenium
    if not result:
        html = scrape_with_selenium(vin)
        if html:
            try:
                result = parse_html(html)
                method_used = 'selenium'
            except Exception as e:
                print(f"Selenium parse error: {str(e)}")
    
    elapsed_time = time.time() - start_time
    
    if result:
        return {
            'success': True,
            'vehicle_info': result['vehicle_info'],
            'sa_codes': result['sa_codes'],
            'time': round(elapsed_time, 2),
            'vin': vin,
            'method': method_used
        }
    else:
        return {
            'success': False,
            'error': "All scraping methods failed. Website protections are too strong.",
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
