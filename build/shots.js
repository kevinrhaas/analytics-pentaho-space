// shots.js — render each dashboard on the Pentaho server and screenshot it into
// ../assets/dashboards/. Used by update-site.sh to keep analytics.pentaho.space showing
// the REAL dashboards.
//
// Works against localhost OR the cloud server (server.pentaho.space). In a cloud session two
// things break naive screenshotting, so this handles both when HTTPS_PROXY is set:
//   1. Chromium's net stack can't reach the localhost egress proxy → every request is served
//      through Playwright's proxy-aware request context instead.
//   2. The server's fully-qualified-server-url is http → CDF emits http:// script tags an https
//      page blocks as Mixed Content → we rewrite http://<host> → https://<host> in served html/js.
//
// Server URL: argv[2] || PENTAHO_URL || dashboards.json "server". Password: PENTAHO_PASS || "password"
// (never hardcode the cloud password here — this repo is public). Run:
//   PENTAHO_PASS=... NODE_PATH=/opt/node22/lib/node_modules node build/shots.js https://server.pentaho.space/pentaho
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const M = JSON.parse(fs.readFileSync(path.join(__dirname, 'dashboards.json'), 'utf8'));
const OUT = path.join(__dirname, '..', 'assets', 'dashboards');
fs.mkdirSync(OUT, { recursive: true });

const SERVER = (process.argv[2] || process.env.PENTAHO_URL || M.server).replace(/\/$/, '');
const PASS = process.env.PENTAHO_PASS || M.password || 'password';
const PROXY = process.env.HTTPS_PROXY || '';
const ORIGIN = SERVER.replace(/\/pentaho$/, '');
const ORIGIN_H = ORIGIN.replace(/^https:/, 'http:');
const CHROME = process.env.PW_CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const targets = [];
targets.push({ stem: M.launcher.stem, full: false });
for (const g of M.groups) for (const it of g.items) targets.push({ stem: it.stem, full: true });

(async () => {
  const launchOpts = { args: ['--no-sandbox', '--disable-dev-shm-usage'] };
  if (fs.existsSync(CHROME)) launchOpts.executablePath = CHROME; else launchOpts.channel = 'chrome';
  if (PROXY) launchOpts.proxy = { server: PROXY };
  const browser = await chromium.launch(launchOpts);
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1,
    ignoreHTTPSErrors: true, proxy: PROXY ? { server: PROXY } : undefined
  });
  const api = ctx.request;
  await api.post(`${SERVER}/j_spring_security_check`,
    { form: { j_username: 'admin', j_password: PASS }, maxRedirects: 0, failOnStatusCode: false });
  const page = await ctx.newPage();
  // In the cloud (proxy set) serve every request through the proxy-aware request context + rewrite http->https.
  if (PROXY) {
    await page.route('**/*', async (route) => {
      const req = route.request(); const u = req.url();
      if (!u.startsWith(ORIGIN) && !u.startsWith(ORIGIN_H)) return route.continue().catch(() => route.abort());
      try {
        const resp = await api.fetch(u.replace(ORIGIN_H, ORIGIN),
          { method: req.method(), headers: req.headers(), data: req.postDataBuffer() || undefined, maxRedirects: 5, failOnStatusCode: false });
        let body = await resp.body(); const h = resp.headers(); delete h['content-encoding']; delete h['content-length'];
        if (/javascript|html|json/.test(h['content-type'] || '')) body = Buffer.from(body.toString('utf8').split(ORIGIN_H).join(ORIGIN));
        await route.fulfill({ status: resp.status(), headers: h, body });
      } catch (e) { route.abort().catch(() => {}); }
    });
  }
  let ok = 0, fail = 0;
  for (const t of targets) {
    const url = `${SERVER}/api/repos/${M.repo}${t.stem}.html/content?cb=${Date.now()}`;
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 40000 });
      await page.waitForFunction(() => document.querySelectorAll('svg').length > 0, { timeout: 25000 }).catch(() => {});
      await page.waitForTimeout(3800);                 // let charts finish drawing
      const out = path.join(OUT, t.stem + '.jpg');
      await page.screenshot({ path: out, fullPage: t.full, type: 'jpeg', quality: 80 });
      const kb = Math.round(fs.statSync(out).size / 1024);
      console.log(`  ✓ ${t.stem}  (${kb} KB)`);
      ok++;
    } catch (e) {
      console.log(`  ✗ ${t.stem}  ${String(e).slice(0, 80)}`);
      fail++;
    }
  }
  console.log(`shots: ${ok} ok, ${fail} failed  (server ${SERVER})`);
  await browser.close();
  process.exit(fail > ok ? 1 : 0);
})();
