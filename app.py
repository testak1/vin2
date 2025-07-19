import random
import time
import os
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

app = Flask(__name__)

# Configuration
REQUEST_DELAY = (3, 7)  # Random delay between 3-7 seconds
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def get_chrome_driver():
    """Configure and return a Chrome WebDriver instance"""
    options = Options()
    
    # Use Render's pre-installed Chrome
    options.binary_location = os.getenv('CHROME_BIN', '/opt/render/.cache/chromium/chrome')
    
    # Headless configuration
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Use Render's ChromeDriver
    service = Service(
        executable_path=os.getenv('CHROMEDRIVER_PATH', '/opt/render/.cache/chromium/chromedriver')
    )
    
    return webdriver.Chrome(service=service, options=options)

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
    result = None
    driver = None
    
    try:
        # Respectful delay
        time.sleep(random.uniform(*REQUEST_DELAY))
        
        driver = get_chrome_driver()
        url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
        driver.get(url)
        
        # Wait for page to load or Cloudflare challenge
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-hover"))
            )
        except TimeoutException:
            if "Checking your browser" in driver.page_source:
                raise Exception("Cloudflare challenge detected")
            raise Exception("Page load timeout")
        
        html = driver.page_source
        result = parse_html(html)
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'time': round(time.time() - start_time, 2),
            'vin': vin
        }
    finally:
        if driver:
            driver.quit()
    
    return {
        'success': True,
        'vehicle_info': result['vehicle_info'],
        'sa_codes': result['sa_codes'],
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
