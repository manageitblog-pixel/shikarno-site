// Запис екрана реальної сторінки для довгих відео: прокрутка до фраз, підсвітка, курсор.
// node rec.js <url> <out.mp4> "фраза1|фраза2" [секунд_на_фразу=4]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const { execSync } = require('child_process');
(async () => {
  const [url, out, phrases = '', per = '4'] = process.argv.slice(2);
  const dir = fs.mkdtempSync('/tmp/rec-');
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1600, height: 1000 }, recordVideo: { dir, size: { width: 1600, height: 1000 } }, locale: 'en-US', deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }); await p.waitForTimeout(2500);
  // прибрати cookie-банери
  for (const t of ['Accept all', 'Accept', 'I agree', 'Got it', 'Allow all']) { try { await p.getByRole('button', { name: t, exact: true }).first().click({ timeout: 800 }); break; } catch (e) {} }
  await p.addStyleTag({ content: '.__hl{outline:5px solid #FFD60A!important;background:rgba(255,214,10,.25)!important;border-radius:6px;transition:all .3s} #__cur{position:fixed;z-index:999999;width:28px;height:28px;pointer-events:none;transition:left .9s ease,top .9s ease}' });
  await p.evaluate(() => { const c = document.createElement('div'); c.id = '__cur'; c.innerHTML = '<svg viewBox="0 0 24 24" width="28" height="28"><path d="M3 2l7 19 2.5-7.5L20 11z" fill="white" stroke="black" stroke-width="1.5"/></svg>'; c.style.left = '800px'; c.style.top = '500px'; document.body.appendChild(c); });
  await p.waitForTimeout(1200);
  for (const ph of phrases.split('|').filter(Boolean)) {
    const ok = await p.evaluate(async (ph) => {
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { if (n.textContent.includes(ph) && n.parentElement.offsetParent !== null) break; }
      if (!n) return false; const el = n.parentElement;
      const y = el.getBoundingClientRect().top + window.scrollY - 330;
      const start = window.scrollY, t0 = performance.now(), D = 1400;
      await new Promise(r => { const step = (t) => { const k = Math.min(1, (t - t0) / D), e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; window.scrollTo(0, start + (y - start) * e); k < 1 ? requestAnimationFrame(step) : r(); }; requestAnimationFrame(step); });
      document.querySelectorAll('.__hl').forEach(e => e.classList.remove('__hl'));
      const r = el.getBoundingClientRect(); const c = document.getElementById('__cur'); c.style.left = (r.left + Math.min(r.width, 300) * 0.6) + 'px'; c.style.top = (r.top + r.height * 0.7) + 'px';
      setTimeout(() => el.classList.add('__hl'), 900); return true;
    }, ph);
    if (!ok) console.error('NOT FOUND:', ph);
    await p.waitForTimeout(parseFloat(per) * 1000);
  }
  await p.waitForTimeout(800);
  const v = p.video(); await ctx.close(); await b.close();
  const webm = await v.path();
  execSync(`ffmpeg -y -loglevel error -i ${webm} -an -c:v libx264 -crf 20 -pix_fmt yuv420p -r 30 ${out}`);
  console.log('OK', out, execSync(`ffprobe -v error -show_entries format=duration -of csv=p=0 ${out}`).toString().trim());
})();
