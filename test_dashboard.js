const puppeteer = require('puppeteer');

(async () => {
  console.log("Starting dashboard test...");
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  
  try {
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle0' });
    console.log("Dashboard loaded.");

    // Check Stats
    const totalApps = await page.$eval('div[style*="color: #333"]', el => el.textContent);
    console.log(`Total Apps displayed: ${totalApps}`);

    const completedCount = await page.$eval('div[style*="color: #0070f3"]', el => el.textContent);
    console.log(`Completed Apps displayed in header: ${completedCount}`);

    // Click "Show Completed Only"
    // Find checkbox by label text or type
    const checkbox = await page.$('input[type="checkbox"]');
    if (checkbox) {
        await checkbox.click();
        console.log("Clicked 'Show Completed Only'.");
        
        // Wait for filter to apply
        await new Promise(r => setTimeout(r, 1000));
        
        // Count rows
        const rows = await page.$$('tbody tr');
        console.log(`Rows visible after filter: ${rows.length}`);
        
        if (rows.length === 0) {
            console.error("FAIL: No rows found after filtering!");
            
            // Check if "No apps found" message exists
            const noAppsMsg = await page.$eval('tbody', el => el.textContent);
            console.log("Table content:", noAppsMsg.trim().substring(0, 100));
        } else {
            console.log("PASS: Found completed apps.");
            // Print first few names
            for (let i = 0; i < Math.min(rows.length, 5); i++) {
                const name = await rows[i].$eval('td:first-child a', el => el.textContent);
                console.log(` - App ${i+1}: ${name}`);
            }
        }
    } else {
        console.error("Checkbox not found!");
    }

  } catch (e) {
    console.error("Test failed:", e);
  } finally {
    await browser.close();
  }
})();














