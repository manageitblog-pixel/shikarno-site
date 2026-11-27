"""Google Ads API — лише читання звітів (власник 27.11 підключив; developer token/MCC з 9.09.2026 не потрібні).
Токен: yt/ads_token.json (окремий OAuth, scope adwords; `python3 auth.py link ads`). Акаунт: 241-710-4356.
  python3 ads.py            → кампанії по днях за 7 днів (покази, кліки, витрати грн, «конверсії» Google)
  python3 ads.py ads        → по оголошеннях (відео) за 7 днів
  python3 ads.py q "<GAQL>" → довільний запит
  python3 ads.py draft      → стан чернетки «Довгі ролики» (кампанія/група/оголошення, статуси)
  python3 ads.py addvideo <VIDEO_ID> "<назва>" → додати оголошення на ПАУЗІ в групу чернетки (спершу validateOnly)
Запис: лише створення зі status PAUSED і завжди validateOnly → реальний запит. Вмикати (ENABLED) — тільки після «так» власника.
Нагадування: «конверсії» Google ≠ підписки YouTube; підписки/години з реклами в YPP не йдуть (strategy.md «YPP: реклама і пороги»).
"""
import json, os, sys, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__))); import yt
CID = "2417104356"; VER = "v23"


C = f"customers/{CID}"
# Чернетка 27.11 (docs/playbooks/google-ads-2026-11-24.md «Чернетка 27.11 (на паузі)»)
DRAFT = dict(campaign="24564765979", ad_group="197743835650", budget="16125577366", audience="366803563")
LOGO, CTA_SUBSCRIBE, CHANNEL_URL = f"{C}/assets/442891864542", f"{C}/assets/442893309108", "https://www.youtube.com/@shikarno_ua"


def call(path, body):
    """POST на REST API; помилка Google Ads → RuntimeError з текстом (без токена)."""
    req = urllib.request.Request(f"https://googleads.googleapis.com/{VER}/{C}/{path}", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + yt.token("ads_token.json"), "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')}") from None


def q(query):
    return call("googleAds:search", {"query": query}).get("results", [])


def mutate(ops):
    """Спершу validateOnly; лише якщо пройшло — той самий запит по-справжньому. ENABLED у запиті — відмова."""
    if '"ENABLED"' in json.dumps(ops):
        raise ValueError("ENABLED заборонено: створюємо лише на паузі")
    call("googleAds:mutate", {"mutateOperations": ops, "validateOnly": True})
    return call("googleAds:mutate", {"mutateOperations": ops})


def draft():
    d = DRAFT
    return (q(f"SELECT campaign.id, campaign.name, campaign.status FROM campaign WHERE campaign.id = {d['campaign']}")
            + q(f"SELECT ad_group.id, ad_group.name, ad_group.status FROM ad_group WHERE campaign.id = {d['campaign']}")
            + q("SELECT ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group_ad.status, ad_group_ad.policy_summary.review_status "
                f"FROM ad_group_ad WHERE campaign.id = {d['campaign']}"))


def add_video_ad(video_id, name, headlines, long_headlines, descriptions, ad_group=DRAFT["ad_group"]):
    """Нове відео-оголошення Demand Gen на ПАУЗІ (відео має бути публічним — інакше VIDEO_NOT_ACCESSIBLE)."""
    vid = f"{C}/assets/-1"
    return mutate([
        {"assetOperation": {"create": {"resourceName": vid, "name": f"YT {video_id}", "youtubeVideoAsset": {"youtubeVideoId": video_id}}}},
        {"adGroupAdOperation": {"create": {"adGroup": f"{C}/adGroups/{ad_group}", "status": "PAUSED", "ad": {
            "name": name, "finalUrls": [CHANNEL_URL], "demandGenVideoResponsiveAd": {
                "headlines": [{"text": t} for t in headlines], "longHeadlines": [{"text": t} for t in long_headlines],
                "descriptions": [{"text": t} for t in descriptions], "videos": [{"asset": vid}],
                "logoImages": [{"asset": LOGO}], "businessName": {"text": "ШІкарно"}, "callToActions": [{"asset": CTA_SUBSCRIBE}]}}}}}])


def campaigns(days="LAST_7_DAYS"):
    out = []
    for x in q("SELECT campaign.name, campaign.status, segments.date, metrics.impressions, metrics.clicks, metrics.cost_micros, "
               f"metrics.conversions FROM campaign WHERE segments.date DURING {days} ORDER BY segments.date"):
        m = x["metrics"]
        out.append(dict(date=x["segments"]["date"], campaign=x["campaign"]["name"], status=x["campaign"]["status"],
                        impressions=int(m.get("impressions", 0)), clicks=int(m.get("clicks", 0)),
                        cost_uah=round(int(m.get("costMicros", 0)) / 1e6, 2), conversions=float(m.get("conversions", 0))))
    return out


def ads(days="LAST_7_DAYS"):
    out = []
    for x in q("SELECT ad_group_ad.ad.id, ad_group_ad.ad.name, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions "
               f"FROM ad_group_ad WHERE segments.date DURING {days}"):
        m = x["metrics"]; a = x["adGroupAd"]["ad"]
        out.append(dict(ad=a.get("name") or a.get("id"), impressions=int(m.get("impressions", 0)), clicks=int(m.get("clicks", 0)),
                        cost_uah=round(int(m.get("costMicros", 0)) / 1e6, 2), conversions=float(m.get("conversions", 0))))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["addvideo"]:
        print("Заголовки/описи задай у виклику add_video_ad() з Python (≤40 / ≤90 знаків)."); sys.exit(1)
    rows = q(a[1]) if a[:1] == ["q"] else ads() if a[:1] == ["ads"] else draft() if a[:1] == ["draft"] else campaigns()
    for r in rows: print(json.dumps(r, ensure_ascii=False))
