import random
import time
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from waitress import serve

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

# Healthy proxies cache
HEALTHY_PROXIES = PROXIES.copy()

def check_proxy_health():
    """Check and update healthy proxies list"""
    global HEALTHY_PROXIES
    working_proxies = []
    
    for proxy in PROXIES:
        try:
            start = time.time()
            requests.get(
                "https://api.ipify.org?format=json",
                proxies=proxy,
                timeout=10
            )
            working_proxies.append(proxy)
            print(f"✅ Proxy {proxy['http']} works ({time.time()-start:.2f}s)")
        except Exception as e:
            print(f"❌ Proxy {proxy['http']} failed: {str(e)}")
    
    HEALTHY_PROXIES = working_proxies or PROXIES  # Fallback to all if none work
    return len(working_proxies)

def get_random_proxy():
    """Get a random proxy from healthy ones"""
    if not HEALTHY_PROXIES:
        check_proxy_health()
    return random.choice(HEALTHY_PROXIES)

def scrape_with_proxy(vin, max_retries=3):
    for attempt in range(max_retries):
        proxy = get_random_proxy()
        try:
            # Random delay (10-30s) to avoid rate limiting
            delay = random.uniform(10, 30)
            print(f"Attempt {attempt+1}: Waiting {delay:.1f}s before request...")
            time.sleep(delay)
            
            response = requests.get(
                f"https://www.vindecoderz.com/EN/check-lookup/{vin}",
                proxies=proxy,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                timeout=30
            )
            
            if response.status_code == 403:
                raise Exception("Cloudflare block (403 Forbidden)")
            if "captcha" in response.text.lower():
                raise Exception("CAPTCHA challenge detected")
                
            return response.text
            
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed via {proxy['http']}: {str(e)}")
            if attempt == max_retries - 1:
                raise

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        vin = request.form['vin'].strip()
        if len(vin) >= 17:
            start_time = time.time()
            try:
                html = scrape_with_proxy(vin)
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parse your data here
                data = {
                    'success': True,
                    'vin': vin,
                    'time': round(time.time() - start_time, 2)
                }
                return render_template('result.html', result=data)
                
            except Exception as e:
                return render_template('error.html', 
                    error=str(e),
                    time=round(time.time() - start_time, 2))
    
    return render_template('index.html')

if __name__ == '__main__':
    # Initial proxy health check
    print(f"Initial proxy check: {check_proxy_health()} working proxies")
    
    # Start production server
    serve(app, host="0.0.0.0", port=5000)
