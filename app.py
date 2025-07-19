from flask import Flask, render_template, request
import cloudscraper
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

def scrape_vin_data(vin):
    scraper = cloudscraper.create_scraper()
    url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
    
    try:
        start_time = time.time()
        response = scraper.get(url, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Exempel på hur du kan extrahera data - anpassa selektorerna
            equipment = []
            equipment_elements = soup.select('.equipment-list li')
            for item in equipment_elements:
                equipment.append(item.text.strip())
            
            return {
                'success': True,
                'equipment': equipment,
                'time': round(elapsed_time, 2),
                'vin': vin
            }
        return {
            'success': False,
            'error': f"HTTP Error {response.status_code}",
            'time': round(elapsed_time, 2)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'time': 0
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
    app.run(debug=True)
