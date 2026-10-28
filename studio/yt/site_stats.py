"""Відвідуваність сайту з Cloudflare Web Analytics (GraphQL, rumPageloadEventsAdaptiveGroups).
  CF_TOKEN=... python3 site_stats.py 2026-10-28T00:00:00Z 2026-10-29T00:00:00Z
Токен — Cloudflare API token з «Доступів» (не в git). Мої тестові заходи — з країни US."""
import json, os, sys, urllib.request
A = "ccc1a134eac2c4a3907b41bac24ddccd"
def stats(since, until, by="requestPath countryName"):
    q = '{viewer{accounts(filter:{accountTag:"%s"}){rumPageloadEventsAdaptiveGroups(limit:100,filter:{datetime_geq:"%s",datetime_leq:"%s"},orderBy:[count_DESC]){count sum{visits} dimensions{%s}}}}}' % (A, since, until, by)
    r = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=json.dumps({"query": q}).encode(),
        headers={"Authorization": "Bearer " + os.environ["CF_TOKEN"], "content-type": "application/json"})
    return json.load(urllib.request.urlopen(r))["data"]["viewer"]["accounts"][0]["rumPageloadEventsAdaptiveGroups"]
if __name__ == "__main__":
    for row in stats(sys.argv[1], sys.argv[2]): print(row["count"], row["sum"]["visits"], row["dimensions"])
