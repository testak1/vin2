import os
import random
import time
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from waitress import serve

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Proxy configuration (using your Webshare credentials)
PROXIES = [
    {"http": f"http://wtvsycnr:wwx5rwg1fooq@{ip}"}
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

def get_proxy():
    """Get a random proxy from the list"""
    return random.choice(PROXIES)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/decode', methods=['POST'])
def decode_vin():
    vin = request.form.get('vin', '').strip()
    start_time = time.time()
    
    if len(vin) != 17:
        return render_template('error.html',
            error="Invalid VIN length (must be 17 characters)",
            time=round(time.time() - start_time, 2))
    
    try:
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(
            f"https://www.vindecoderz.com/EN/check-lookup/{vin}",
            proxies=get_proxy(),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            },
            timeout=20
        )
        
        if response.status_code == 200:
            # Add your parsing logic here
            return render_template('result.html',
                vin=vin,
                time=round(time.time() - start_time, 2))
        else:
            return render_template('error.html',
                error=f"HTTP Error {response.status_code}",
                time=round(time.time() - start_time, 2))
                
    except Exception as e:
        return render_template('error.html',
            error=str(e),
            time=round(time.time() - start_time, 2))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting server on port {port}")
    serve(app, host="0.0.0.0", port=port)
