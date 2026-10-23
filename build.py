#!/usr/bin/env python3
"""Збирає статичний сайт ШІкарно: content/*.md -> dist/.
   python3 build.py            — сайт у dist/
   python3 build.py --preview  — один HTML-файл для перегляду (preview.html)"""
import sys, re, json, shutil, datetime as dt
from pathlib import Path
from email.utils import format_datetime
from urllib.parse import quote
import yaml, markdown
from jinja2 import Environment, FileSystemLoader
from config import SITE, TAG_NAMES

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
# без власного домену сайт живе на github.io/shikarno-site/ — тоді всі шляхи з префіксом
BASE = "" if SITE.get("domain") else SITE.get("project_base", "")
KINDS = {  # тип матеріалу → (розділ URL, назва розділу, мітка в стрічці)
    "news":      ("novyny",    "Новини",          None),
    "rozbir":    ("rozbory",   "Розбори",         "Розбір"),
    "dajdzhest": ("dajdzhest", "Дайджести тижня", "Дайджест"),
    "misyats":   ("za-misyats","ШІ за місяць",    "ШІ за місяць"),
}
MONTHS = ["січня","лютого","березня","квітня","травня","червня","липня","серпня","вересня","жовтня","листопада","грудня"]

def load(md_path):
    raw = md_path.read_text(encoding="utf-8")
    _, fm, body = raw.split("---", 2)
    meta = yaml.safe_load(fm)
    html = markdown.markdown(body.strip(), extensions=["extra", "sane_lists"])
    meta["html"] = html.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    return meta

def to_sec(t):
    n = 0
    for part in str(t).split(":"): n = n*60 + int(part)
    return n

def human(d): return f"{d.day} {MONTHS[d.month-1]} {d.year}"
def tagname(t): return TAG_NAMES.get(t, t)
def plural(n):
    if n % 10 == 1 and n % 100 != 11: return "матеріал"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14: return "матеріали"
    return "матеріалів"

def posts_all():
    out = []
    for f in sorted((ROOT/"content/posts").glob("*.md")):
        p = load(f)
        if p.get("draft"): continue
        d = p["date"] if isinstance(p["date"], dt.datetime) else dt.datetime.fromisoformat(str(p["date"]))
        if d > dt.datetime.now(dt.timezone.utc) and "--future" not in sys.argv: continue  # відкладена публікація
        kind = p.get("kind", "news"); sec, sec_name, label = KINDS[kind]
        p.update(kind=kind, sec=sec, sec_name=sec_name, label=label, long=kind != "news")
        u = p.get("updated"); u = u if isinstance(u, dt.datetime) else (dt.datetime.fromisoformat(str(u)) if u else d)
        words = len(re.sub(r"<[^>]+>", " ", p["html"]).split())
        p.update(dt=d, iso=d.isoformat(), human=human(d), path=f"/{sec}/{p['slug']}/",
                 upd_iso=u.isoformat(), upd_human=human(u), words=words, minutes=max(1, round(words/180)))
        out.append(p)
    return sorted(out, key=lambda p: p["dt"], reverse=True)

ORG = {"@type": "Organization", "name": SITE["name"], "url": SITE["url"],
       "logo": {"@type": "ImageObject", "url": SITE["url"] + "/static/logo.png"},
       "sameAs": [SITE["youtube"], SITE["telegram"]]}

def post_ld(p):
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "NewsArticle", "headline": p["title"], "description": p["description"],
         "datePublished": p["iso"], "dateModified": p["upd_iso"], "wordCount": p["words"],
         "inLanguage": "uk", "mainEntityOfPage": SITE["url"] + p["path"],
         "author": ORG, "publisher": ORG, "keywords": [tagname(t) for t in p["tags"]],
         "isBasedOn": p["source"]["url"]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": p["sec_name"], "item": SITE["url"] + "/" + p["sec"] + "/"},
            {"@type": "ListItem", "position": 2, "name": p["title"], "item": SITE["url"] + p["path"]}]}]}
    if p.get("faq"):
        ld["@graph"].append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in p["faq"]]})
    if p.get("youtube"):
        y = p["youtube"]
        vid = {"@type": "VideoObject", "name": p["title"], "description": p["description"],
               "thumbnailUrl": f"https://i.ytimg.com/vi/{y}/hqdefault.jpg", "uploadDate": p["iso"],
               "embedUrl": f"https://www.youtube.com/embed/{y}",
               "contentUrl": f"https://www.youtube.com/{'watch?v=' if p['long'] else 'shorts/'}{y}"}
        if p.get("chapters"):
            secs = [to_sec(c["t"]) for c in p["chapters"]]
            vid["hasPart"] = [{"@type": "Clip", "name": c["title"], "startOffset": secs[i],
                               **({"endOffset": secs[i+1]} if i+1 < len(secs) else {}),
                               "url": f"https://www.youtube.com/watch?v={y}&t={secs[i]}s"} for i, c in enumerate(p["chapters"])]
        ld["@graph"][0]["video"] = vid
        ld["@graph"][0]["image"] = vid["thumbnailUrl"]
    return json.dumps(ld, ensure_ascii=False)

def build(preview=False):
    env = Environment(loader=FileSystemLoader(ROOT/"templates"), autoescape=True)
    posts = posts_all()
    pages = [load(f) for f in sorted((ROOT/"content/pages").glob("*.md"))]
    tags = {}
    for p in posts:
        for t in p["tags"]: tags.setdefault(t, []).append(p)

    def token(path):
        if path == "/": return "#home"
        m = re.match(r"/(?:novyny|rozbory|dajdzhest|za-misyats)/([^/]+)/", path)
        if m: return "#p-" + m.group(1)
        m = re.match(r"/teg/([^/]+)/", path)
        if m: return "#t-" + m.group(1)
        return "#" + path.strip("/")
    env.globals.update(to_sec=to_sec, site=SITE, year=dt.date.today().year, tagname=tagname, plural=plural,
                       u=(token if preview else (lambda x: BASE + x)), bare=preview, base=BASE)
    env.filters["urlencode"] = lambda s: quote(str(s), safe="")

    views = []  # (path, html)
    def emit(path, tpl, **ctx):
        views.append((path, env.get_template(tpl).render(path=path, **ctx)))

    home_ld = json.dumps({"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": SITE["name"], "url": SITE["url"] + "/", "inLanguage": "uk", "description": SITE["description"]},
        ORG]}, ensure_ascii=False)
    emit("/", "index.html", posts=posts, page_title=f"{SITE['name']} — новини штучного інтелекту українською",
         page_desc=SITE["description"], jsonld=home_ld)
    for p in posts:
        rel = [q for q in posts if q is not p and set(q["tags"]) & set(p["tags"])][:3]
        emit(p["path"], "post.html", p=p, related=rel, page_title=f"{p['title']} | {SITE['name']}",
             page_desc=p["description"], og_type="article", jsonld=post_ld(p),
             og_image=f"https://i.ytimg.com/vi/{p['youtube']}/hqdefault.jpg" if p.get("youtube") else None)
    for t, items in sorted(tags.items()):
        emit(f"/teg/{t}/", "tag.html", tag_title=tagname(t), items=items,
             page_title=f"{tagname(t)}: новини ШІ українською | {SITE['name']}",
             page_desc=f"Усі матеріали ШІкарно на тему «{tagname(t)}»: коротко, з джерелами і вердиктом Байта.")
    for kind, (sec, sec_name, _) in KINDS.items():
        items = [p for p in posts if p["kind"] == kind]
        emit(f"/{sec}/", "tag.html", tag_title=sec_name, items=items if kind != "news" else posts,
             page_title=f"{sec_name} | {SITE['name']}", page_desc=f"{sec_name} ШІкарно: штучний інтелект українською, з джерелами і вердиктом Байта.")
    for pg in pages:
        emit(f"/{pg['slug']}/", "page.html", pg=pg, page_title=f"{pg['title']} | {SITE['name']}", page_desc=pg["description"])
    emit("/404/", "404.html", page_title=f"Сторінку не знайдено | {SITE['name']}", page_desc=SITE["description"])

    if preview: return write_preview(env, views)

    shutil.rmtree(DIST, ignore_errors=True)
    for path, html in views:
        out = DIST / ("404.html" if path == "/404/" else path.strip("/") + "/index.html" if path != "/" else "index.html")
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html, encoding="utf-8")
    shutil.copytree(ROOT/"static", DIST/"static")
    # sitemap, rss, robots
    urls = [(path, None) for path, _ in views if path != "/404/"]
    last = {p["path"]: p["iso"] for p in posts}
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, _ in urls:
        lm = last.get(path, posts[0]["iso"] if posts else None)
        sm.append(f"<url><loc>{SITE['url']}{path}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + "</url>")
    sm.append("</urlset>")
    (DIST/"sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    from xml.sax.saxutils import escape as x
    items = "".join(f"<item><title>{x(p['title'])}</title><link>{SITE['url']}{p['path']}</link><guid>{SITE['url']}{p['path']}</guid>"
                    f"<pubDate>{format_datetime(p['dt'])}</pubDate><description>{x(p['description'])}</description></item>" for p in posts[:30])
    (DIST/"rss.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{SITE["name"]}</title>'
        f'<link>{SITE["url"]}/</link><description>{x(SITE["description"])}</description><language>uk</language>{items}</channel></rss>', encoding="utf-8")
    (DIST/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n")
    if SITE.get("domain"): (DIST/"CNAME").write_text(SITE["domain"] + "\n")
    print(f"dist/: {len(views)} сторінок, {len(posts)} постів, {len(tags)} тегів")

def write_preview(env, views):
    css = (ROOT/"static/style.css").read_text(encoding="utf-8")
    js = (ROOT/"static/site.js").read_text(encoding="utf-8")
    chrome_top = env.get_template("chrome_top.html").render()
    chrome_bottom = env.get_template("chrome_bottom.html").render()
    def tok(path): return env.globals["u"](path).lstrip("#") if path != "/404/" else "404"
    secs = "".join(f'<div class="view" data-view="{tok(p)}" hidden>{h}</div>' for p, h in views)
    router = """function show(){var t=(location.hash||'#home').slice(1);var v=document.querySelector('.view[data-view="'+t+'"]')||document.querySelector('.view[data-view="home"]');
document.querySelectorAll('.view').forEach(function(e){e.hidden=e!==v});window.scrollTo(0,0);}
addEventListener('hashchange',show);show();"""
    html = f"""<!doctype html><html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>ШІкарно — сайт (прев'ю)</title>
<link href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600&family=Montserrat:wght@800;900&display=swap" rel="stylesheet">
<style>{css}</style></head><body>{chrome_top}{secs}{chrome_bottom}<script>{js}\n{router}</script></body></html>"""
    out = ROOT/"preview.html"; out.write_text(html, encoding="utf-8"); print("preview.html", len(html)//1024, "КБ")

if __name__ == "__main__":
    build(preview="--preview" in sys.argv)
