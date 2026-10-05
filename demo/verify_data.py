#!/usr/bin/env python3
"""Runs every panel query of every provisioned dashboard through Grafana and fails if any returns no rows.
Usage: GRAFANA_URL=http://localhost:3000 GRAFANA_AUTH=admin:<password> ./verify_data.py"""
import base64, json, os, sys, urllib.request

URL = os.environ.get("GRAFANA_URL", "http://localhost:3000")
AUTH = base64.b64encode(os.environ.get("GRAFANA_AUTH", "admin:admin").encode()).decode()


def call(path, body=None):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}") | {"_http": e.code}


bad = total = 0
for hit in call("/api/search?type=dash-db"):
    d = call("/api/dashboards/uid/" + hit["uid"])["dashboard"]
    for p in d["panels"]:
        if p.get("datasource", {}).get("uid") == "grafana":
            continue  # Business Variable: no query
        queries = []
        for t in p["targets"]:
            t = json.loads(json.dumps(t).replace("$host", "web"))
            t["intervalMs"], t["maxDataPoints"] = 60000, 500
            queries.append(t)
        r = call("/api/ds/query", {"queries": queries, "from": d["time"]["from"], "to": d["time"]["to"]})
        for ref, res in r.get("results", {}).items():
            total += 1
            rows = sum(len(f["data"]["values"][0]) if f["data"]["values"] else 0 for f in res.get("frames", []))
            if res.get("error") or rows == 0:
                bad += 1
                print(f"FAIL {d['title']} / {p['title']} [{ref}]: rows={rows} err={res.get('error')}")
        if not r.get("results"):
            bad += 1; total += 1
            print(f"FAIL {d['title']} / {p['title']}: {r}")
print(f"{total - bad}/{total} queries returned data")
sys.exit(1 if bad else 0)
