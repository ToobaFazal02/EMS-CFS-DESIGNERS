const { chromium } = require("playwright");
const fs = require("fs");

(async () => {
  const out = "D:/imp/ems-cfs-designers/docs/client-demo";
  fs.mkdirSync(out, { recursive: true });
  let browser;
  try {
    browser = await chromium.launch({ channel: "chrome", headless: true });
  } catch {
    try {
      browser = await chromium.launch({ channel: "msedge", headless: true });
    } catch {
      browser = await chromium.launch({ headless: true });
    }
  }
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto("http://127.0.0.1:5173/login", { waitUntil: "domcontentloaded", timeout: 20000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${out}/01-login.png` });
  await page.fill("#email", "admin@cfsdesigners.com");
  await page.fill("#password", "Admin123!");
  await page.click('button[type=submit]');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}/02-live.png` });
  await page.goto("http://127.0.0.1:5173/employees", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}/03-employees.png` });
  await page.goto("http://127.0.0.1:5173/reports", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${out}/04-reports.png` });
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  const day = page.locator('a[href*="/day/"]').first();
  if (await day.count()) {
    await day.click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${out}/05-day-detail.png`, fullPage: true });
  }
  await browser.close();
  console.log("SHOTS_OK");
  console.log(fs.readdirSync(out).join(","));
})().catch((e) => {
  console.error("FAIL", e);
  process.exit(1);
});
