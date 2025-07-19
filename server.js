const express = require('express');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const app = express();
const PORT = process.env.PORT || 3000;

puppeteer.use(StealthPlugin());

app.use(express.json());

app.post('/decode', async (req, res) => {
    const { vin } = req.body;

    if (!vin) return res.status(400).send('VIN missing');

    try {
        const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const page = await browser.newPage();
        await page.goto(`https://www.vindecoderz.com/EN/check-lookup/${vin}`, { waitUntil: 'networkidle2' });

        // Example: wait and extract table
        await page.waitForSelector('.panel-body'); // adjust selector as needed
        const content = await page.content();

        await browser.close();
        res.send(content); // or parse and extract structured data
    } catch (err) {
        console.error(err);
        res.status(500).send('Error decoding VIN');
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
