const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const html = path.resolve(__dirname, 'screens.html');
  const outDir = path.resolve(__dirname, '..');
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
  });
  const page = await browser.newPage({
    viewport: { width: 1400, height: 1000 },
    deviceScaleFactor: 2,
  });
  await page.goto('file://' + html, { waitUntil: 'networkidle' });

  const map = {
    home: 'mockup-00-home.png',
    select: 'mockup-01-select.png',
    chat: 'mockup-01b-chat.png',
    range: 'mockup-02-range.png',
    config: 'mockup-03-config.png',
    pdf: 'mockup-04-pdf.png',
    upload: 'mockup-05-upload.png',
    result: 'mockup-06-result.png',
  };

  for (const [id, file] of Object.entries(map)) {
    const el = page.locator('#' + id);
    await el.screenshot({ path: path.join(outDir, file), type: 'png' });
    console.log('wrote', file);
  }

  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
