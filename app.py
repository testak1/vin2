import os
import random
import time
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from waitress import serve  # Production WSGI server

app = Flask(__name__)

# Configuration
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

# Production settings
PORT = int(os.environ.get('PORT', 5000))  # Render provides PORT environment variable
REQUEST_DELAY = (10, 30)  # Seconds between requests

def get_proxy():
    """Get a random proxy with logging"""
    proxy = random.choice(PROXIES)
    print(f"Using proxy: {proxy['http']}")
    return proxy

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        vin = request.form.get('vin', '').strip()
        if len(vin) >= 17:
            start_time = time.time()
            try:
                # Respectful delay
                time.sleep(random.uniform(*REQUEST_DELAY))
                
                response = requests.get(
                    f"https://www.vindecoderz.com/EN/check-lookup/{vin}",
                    proxies=get_proxy(),
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept-Language': 'en-US,en;q=0.9'
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
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
    
    return render_template('index.html')

if __name__ == '__main__':
    print(f"Starting server on port {PORT}")
    serve(app, host="0.0.0.0", port=PORT)  # Production server
