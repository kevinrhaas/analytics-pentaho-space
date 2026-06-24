// thumbs.js — capture a small thumbnail of every LAUNCHER dashboard for the sexy i-home
// console. Reads stem list from argv[2] (one stem per line) or build/launcher-stems.txt,
// renders each on the local Pentaho server, writes assets/thumbs/<stem>.jpg (viewport, top
// of the dashboard). The launcher references these by URL with a graceful fallback.
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const SERVER = process.env.PENTAHO_SERVER || 'http://localhost:8080/pentaho';
const REPO = ':public:pdc-iteration:v2:';
const OUT = path.join(__dirname, '..', 'assets', 'thumbs');
fs.mkdirSync(OUT, { recursive: true });
const listFile = process.argv[2] || path.join(__dirname, 'launcher-stems.txt');
const stems = fs.readFileSync(listFile, 'utf8').split('\n').map(s => s.trim()).filter(Boolean);
(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const ctx = await browser.newContext({ viewport: { width: 1200, height: 740 }, deviceScaleFactor: 1 });
  await ctx.request.post(`${SERVER}/j_spring_security_check`, { form: { j_username: 'admin', j_password: 'password' } });
  const page = await ctx.newPage();
  let ok = 0, fail = 0;
  for (const stem of stems) {
    try {
      await page.goto(`${SERVER}/api/repos/${REPO}${stem}.html/content?cb=${Date.now()}`, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(3600);
      await page.screenshot({ path: path.join(OUT, stem + '.jpg'), type: 'jpeg', quality: 72, clip: { x: 0, y: 0, width: 1200, height: 720 } });
      ok++; process.stdout.write('.');
    } catch (e) { fail++; process.stdout.write('x'); }
  }
  console.log(`\nthumbs: ${ok} ok, ${fail} failed`);
  await browser.close();
  process.exit(fail > ok ? 1 : 0);
})();
