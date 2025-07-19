import random
import time
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)

# Webshare Proxies Configuration
PROXIES = [
    {"http": f"http://wtvsycnr:wwx5rwg1fooq@{ip}", 
     "https": f"http://wtvsycnr:wwx5rwg1fooq@{ip}"}
    for ip in [
        "38.154.227.167:5868",
        "23.95.150.145:6114",
        "198.23.239.134:6540",
        "45.38.107.97:6014",
        "207.244.217.165:6712",
        "107.172.163.27:6543",
        "216.10.27.159:6837",
        "136.0.207.84:6661",
        "142.147.128.93:6593",
        "206.41.172.74:6634"
    ]
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_random_proxy():
    return random.choice(PROXIES)

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'DNT': '1'
    }

def scrape_with_proxy(vin, max_retries=3):
    for attempt in range(max_retries):
        try:
            proxy = get_random_proxy()
            headers = get_random_headers()
            
            # Add random delay (10-20 seconds)
            time.sleep(random.uniform(10, 20))
            
            response = requests.get(
                f"https://www.vindecoderz.com/EN/check-lookup/{vin}",
                proxies=proxy,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 403:
                raise Exception("Cloudflare block (403 Forbidden)")
                
            if "captcha" in response.text.lower():
                raise Exception("CAPTCHA challenge detected")
                
            return response.text
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with proxy {proxy['http']}: {str(e)}")
            if attempt == max_retries - 1:
                raise

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    vehicle_info = {
        'brand': safe_extract(soup, 'table.table-hover tr:nth-of-type(4) td:nth-of-type(2)'),
        'model': safe_extract(soup, 'table.table-hover tr:nth-of-type(6) td:nth-of-type(2)'),
        'year': safe_extract(soup, 'h2 strong', lambda x: x.get_text().split()[-1])
    }
    
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
    try:
        element = soup.select_one(selector)
        return transform(element) if transform and element else element.get_text(strip=True) if element else None
    except:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        vin = request.form.get('vin', '').strip()
        if len(vin) >= 17:
            try:
                start_time = time.time()
                html = scrape_with_proxy(vin)
                data = parse_html(html)
                result = {
                    'success': True,
                    'data': data,
                    'time': round(time.time() - start_time, 2)
                }
            except Exception as e:
                result = {
                    'success': False,
                    'error': str(e),
                    'time': 0
                }
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run()
