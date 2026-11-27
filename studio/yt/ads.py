"""Google Ads API — лише читання звітів (власник 27.11 підключив; developer token/MCC з 9.09.2026 не потрібні).
Токен: yt/ads_token.json (окремий OAuth, scope adwords; `python3 auth.py link ads`). Акаунт: 241-710-4356.
  python3 ads.py            → кампанії по днях за 7 днів (покази, кліки, витрати грн, «конверсії» Google)
  python3 ads.py ads        → по оголошеннях (відео) за 7 днів
  python3 ads.py q "<GAQL>" → довільний запит
Нагадування: «конверсії» Google ≠ підписки YouTube; підписки/години з реклами в YPP не йдуть (strategy.md «YPP: реклама і пороги»).
"""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__))); import yt
CID = "2417104356"; VER = "v23"


def q(query):
    req = urllib.request.Request(f"https://googleads.googleapis.com/{VER}/customers/{CID}/googleAds:search",
                                 json.dumps({"query": query}).encode(),
                                 {"Authorization": "Bearer " + yt.token("ads_token.json"), "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60)).get("results", [])


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
    rows = q(a[1]) if a[:1] == ["q"] else ads() if a[:1] == ["ads"] else campaigns()
    for r in rows: print(json.dumps(r, ensure_ascii=False))
