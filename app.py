from flask import Flask, render_template, request
import cloudscraper
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

def scrape_vin_data(vin):
    scraper = cloudscraper.create_scraper()
    url = f"https://www.vindecoderz.com/EN/check-lookup/{vin}"
    
    try:
        response = scraper.get(url, timeout=30)
        
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
            
            # The main SA codes table is typically the second table with this class
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
                'vin': vin
            }
            
        return {
            'success': False,
            'error': f"HTTP Error {response.status_code}",
            'vin': vin
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
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
