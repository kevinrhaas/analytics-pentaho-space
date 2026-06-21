// shots.js — render each dashboard on the local Pentaho server and screenshot it into
// ../assets/dashboards/. Used by update-site.sh to keep analytics.pentaho.space showing
// the REAL dashboards. Requires the local server up (localhost:8080) with the v2 suite deployed.
// Run from the build/ dir:  node shots.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const M = JSON.parse(fs.readFileSync(path.join(__dirname, 'dashboards.json'), 'utf8'));
const OUT = path.join(__dirname, '..', 'assets', 'dashboards');
fs.mkdirSync(OUT, { recursive: true });

const targets = [];
targets.push({ stem: M.launcher.stem, full: false });
for (const g of M.groups) for (const it of g.items) targets.push({ stem: it.stem, full: true });

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  await ctx.request.post(`${M.server}/j_spring_security_check`, { form: { j_username: 'admin', j_password: 'password' } });
  const page = await ctx.newPage();
  let ok = 0, fail = 0;
  for (const t of targets) {
    const url = `${M.server}/api/repos/${M.repo}${t.stem}.html/content?cb=${Date.now()}`;
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(3800);                 // let charts draw
      const out = path.join(OUT, t.stem + '.png');
      await page.screenshot({ path: out, fullPage: t.full });
      const kb = Math.round(fs.statSync(out).size / 1024);
      console.log(`  ✓ ${t.stem}  (${kb} KB)`);
      ok++;
    } catch (e) {
      console.log(`  ✗ ${t.stem}  ${String(e).slice(0, 80)}`);
      fail++;
    }
  }
  console.log(`shots: ${ok} ok, ${fail} failed`);
  await browser.close();
  process.exit(fail > ok ? 1 : 0);
})();
