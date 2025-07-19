const express = require('express');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const path = require('path');
const app = express();

puppeteer.use(StealthPlugin());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

app.post('/decode', async (req, res) => {
  const { vin } = req.body;
  if (!vin) return res.status(400).json({ error: 'VIN missing' });

  try {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    const url = `https://www.vindecoderz.com/EN/check-lookup/${vin}`;
    await page.goto(url, { waitUntil: 'networkidle2' });

    await page.waitForSelector('.table.table-striped.table-hover', { timeout: 15000 });

    const equipment = await page.$$eval('.table.table-striped.table-hover tbody tr', rows => {
      return rows.map(row => {
        const code = row.querySelector('b')?.innerText || '';
        const description = row.querySelectorAll('td')[1]?.innerText.trim() || '';
        return { code, description };
      }).filter(item => item.code && item.description);
    });

    await browser.close();
    res.json({ equipment });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to fetch or parse data' });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Server is running on port ${PORT}`));
