// Скрін першоджерела для сегмента evidence: node shots.js <url> <out.png> ["текст для підсвітки"] → друкує JSON {image, hl}
// Запуск: NODE_PATH=$(npm root -g) node /home/claude/eps/shots.js URL /home/claude/rv/public/shots/name.png "Skills"
const { chromium } = require('playwright');
(async () => {
  const [url, out, text] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1600, height: 1000 }, locale: 'uk-UA' });
  await p.goto(url, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => {});
  await p.waitForTimeout(1500);
  let hl = null;
  if (text) {
    const loc = p.getByText(text, { exact: false }).first();
    try { await loc.scrollIntoViewIfNeeded({ timeout: 5000 }); await p.evaluate(() => window.scrollBy(0, -250)); await p.waitForTimeout(500);
          const bb = await loc.boundingBox(); if (bb) hl = { x: Math.round(bb.x), y: Math.round(bb.y), w: Math.round(bb.width), h: Math.round(bb.height) }; } catch (e) {}
  }
  await p.screenshot({ path: out });
  await b.close();
  console.log(JSON.stringify({ image: 'shots/' + out.split('/').pop(), hl }));
})();
