from flask import Flask, render_template, request
import cloudscraper
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

def scrape_vin_data(vin):
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.vindecoderz.com/'
    }

    url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
    
    try:
        start_time = time.time()
        response = scraper.get(url, headers=headers, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic vehicle info
            vehicle_info = {
                'brand': soup.select_one('table.table-hover tr:nth-of-type(4) td:nth-of-type(2)').get_text(strip=True),
                'model': soup.select_one('table.table-hover tr:nth-of-type(6) td:nth-of-type(2)').get_text(strip=True),
                'year': soup.select_one('h2 strong').get_text().split()[-1] if soup.select_one('h2 strong') else None
            }
            
            # Extract SA codes (equipment)
            sa_codes = []
            sa_table = soup.select('div.section table.table-striped')
            
            if len(sa_table) > 1:
                rows = sa_table[1].select('tbody tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        code = cells[0].get_text(strip=True)
                        description = cells[1].get_text(strip=True)
                        sa_codes.append({
                            'code': code,
                            'description': description
                        })
            
            return {
                'success': True,
                'vehicle_info': vehicle_info,
                'sa_codes': sa_codes,
                'time': round(elapsed_time, 2),  # Add this line
                'vin': vin
            }
            
        return {
            'success': False,
            'error': f"HTTP Error {response.status_code}",
            'time': round(elapsed_time, 2),  # Add this line
            'vin': vin
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'time': 0,  # Add this line
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
    app.run(host='0.0.0.0', port=5000)
