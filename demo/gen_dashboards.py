#!/usr/bin/env python3
"""Generates demo dashboards (provisioning/dashboards/json/*.json) from one panel library."""
import copy
import json
import pathlib

OUT = pathlib.Path(__file__).parent / "provisioning/dashboards/json"
TABLE_TPL = pathlib.Path(__file__).parent.parent / "provisioning/dashboards/business-table/simple.json"

CH = {"type": "grafana-clickhouse-datasource", "uid": "ch"}
PROM = {"type": "prometheus", "uid": "prom"}
INF = {"type": "yesoreyeram-infinity-datasource", "uid": "inf"}
GRAFANA = {"type": "datasource", "uid": "grafana"}

HOSTS = "web,api,db"


def chq(sql, fmt=1):
    return [{"refId": "A", "datasource": CH, "editorType": "sql", "rawSql": sql, "format": fmt}]


def promq(expr, legend="", ref="A"):
    return {"refId": ref, "datasource": PROM, "expr": expr, "legendFormat": legend, "range": True, "instant": False}


def panel(type_, title, ds, targets, options=None, fieldConfig=None, desc=""):
    p = {"type": type_, "title": title, "datasource": ds, "targets": targets, "description": desc}
    if options is not None:
        p["options"] = options
    if fieldConfig is not None:
        p["fieldConfig"] = fieldConfig
    return p


def table_options(cols):
    o = copy.deepcopy(json.load(open(TABLE_TPL))["panels"][0]["options"])
    t = o["tables"][0]
    tpl = t["items"][0]
    t["items"] = []
    for c in cols:
        it = copy.deepcopy(tpl)
        it["field"] = {"name": c, "source": "A"}
        t["items"].append(it)
    return o


# ---- panel library -----------------------------------------------------------------------------
def p_table_ch():
    return panel("volkovlabs-table-panel", "Business Table: latest metrics (ClickHouse)", CH,
                 chq("SELECT ts, host, cpu, mem, rps FROM demo.metrics WHERE $__timeFilter(ts) ORDER BY ts DESC LIMIT 100"),
                 table_options(["ts", "host", "cpu", "mem", "rps"]))


def p_table_inf():
    t = {"refId": "A", "datasource": INF, "type": "json", "source": "url", "format": "table", "parser": "backend",
         "url": "http://prometheus:9090/api/v1/targets", "root_selector": "data.activeTargets",
         "url_options": {"method": "GET", "data": "", "params": [], "headers": []},
         "columns": [{"selector": "labels.job", "text": "job", "type": "string"},
                     {"selector": "health", "text": "health", "type": "string"},
                     {"selector": "scrapeUrl", "text": "url", "type": "string"},
                     {"selector": "lastScrapeDuration", "text": "duration_s", "type": "number"}]}
    return panel("volkovlabs-table-panel", "Business Table: Prometheus targets (Infinity)", INF, [t],
                 table_options(["job", "health", "url", "duration_s"]))


def p_charts():
    js = ("const f=context.panel.data.series[0].fields; const get=n=>f.find(x=>x.name===n).values;"
          "const ts=get('ts'), host=get('host'), cpu=get('cpu'); const hosts=[...new Set(host)];"
          "const times=[...new Set(ts)].sort((a,b)=>a-b);"
          "return {tooltip:{trigger:'axis'}, legend:{data:hosts, textStyle:{color:'#ccc'}},"
          "grid:{left:40,right:20,top:40,bottom:30},"
          "xAxis:{type:'category', data:times.map(t=>new Date(t).toLocaleTimeString().slice(0,5))},"
          "yAxis:{type:'value', max:100},"
          "series:hosts.map(h=>({name:h, type:'line', smooth:true, showSymbol:false,"
          "data:times.map(t=>{const i=ts.findIndex((x,k)=>x===t&&host[k]===h); return i<0?null:cpu[i];})}))};")
    return panel("volkovlabs-echarts-panel", "Business Charts: CPU by host (ECharts)", CH,
                 chq("SELECT toStartOfFiveMinutes(ts) AS ts, host, round(avg(cpu), 1) AS cpu FROM demo.metrics WHERE $__timeFilter(ts) GROUP BY ts, host ORDER BY ts"),
                 {"getOption": js})


def p_text():
    return panel("marcusolsson-dynamictext-panel", "Business Text: host summary (ClickHouse)", CH,
                 chq("SELECT host, round(avg(cpu),1) AS avg_cpu, round(max(cpu),1) AS max_cpu, round(avg(mem),1) AS avg_mem "
                     "FROM demo.metrics WHERE $__timeFilter(ts) GROUP BY host ORDER BY host"),
                 {"renderMode": "allRows", "defaultContent": "no data", "contentPartials": [], "editors": [],
                  "editor": {"language": "html"}, "helpers": "", "afterRender": "", "styles": "",
                  "content": "<div style=\"padding:6px\"><h3>Hosts</h3>"
                             "{{#each data}}<p><b>{{host}}</b> — avg CPU {{avg_cpu}}% · max {{max_cpu}}% · mem {{avg_mem}}%</p>{{/each}}</div>"})


def p_calendar():
    return panel("marcusolsson-calendar-panel", "Business Calendar: deploys & maintenance (ClickHouse)", CH,
                 chq("SELECT title, start, end, kind FROM demo.events"),
                 {"textField": "title", "timeField": "start", "endTimeField": "end", "labelFields": ["kind"],
                  "descriptionField": [], "defaultView": "month", "colors": "event", "dateFormat": "inherit",
                  "views": ["day", "week", "month", "agenda"], "annotations": False, "timeRangeType": "default",
                  "displayFields": ["text", "time", "labels"], "scrollToTime": {"hours": 0, "minutes": 0}})


def p_graphviz_code():
    return panel("grafana-graphviz-panel", "Graphviz: architecture (DOT code)", CH, chq("SELECT 1"),
                 {"inputMode": "code", "layoutEngine": "dot", "rankDirection": "LR", "namedThresholds": [],
                  "edgeOverrides": [], "nodeOverrides": [],
                  "dotDiagram": "digraph G { node [shape=box style=rounded]; client -> web -> api -> db; api -> cache; web -> cdn; }"})


def p_graphviz_query():
    return panel("grafana-graphviz-panel", "Graphviz: diagram from a ClickHouse query", CH,
                 chq("SELECT dot FROM demo.graph"),
                 {"inputMode": "query", "dotDiagram": "", "dotQueryConfig": {"fieldName": "dot"}, "layoutEngine": "dot",
                  "rankDirection": "LR", "namedThresholds": [], "edgeOverrides": [], "nodeOverrides": []})


def p_variable():
    return panel("volkovlabs-variable-panel", "Business Variable: pick a host", GRAFANA,
                 [{"refId": "A", "datasource": GRAFANA}], {"variable": "host"})


def p_ts_ch(metric="cpu", title=None, host_filter=False):
    flt = " AND host = '$host'" if host_filter else ""
    return panel("timeseries", title or f"{metric} by host (ClickHouse)", CH,
                 chq(f"SELECT $__timeInterval(ts) AS time, host, avg({metric}) AS {metric} FROM demo.metrics "
                     f"WHERE $__timeFilter(ts){flt} GROUP BY time, host ORDER BY time", 0),
                 {"legend": {"displayMode": "list", "placement": "bottom"}},
                 {"defaults": {"unit": "percent" if metric != "rps" else "reqps", "custom": {"lineWidth": 2, "fillOpacity": 12}}, "overrides": []})


def p_stat_ch():
    return panel("stat", "Avg CPU (ClickHouse)", CH,
                 chq("SELECT avg(cpu) AS cpu FROM demo.metrics WHERE $__timeFilter(ts)", 1), {"reduceOptions": {"calcs": ["lastNotNull"]}},
                 {"defaults": {"unit": "percent", "decimals": 1, "thresholds": {"mode": "absolute", "steps": [
                     {"color": "green", "value": None}, {"color": "orange", "value": 60}, {"color": "red", "value": 80}]}}, "overrides": []})


def p_bar_ch():
    return panel("bargauge", "Max CPU by host (ClickHouse)", CH,
                 chq("SELECT host, max(cpu) AS max_cpu FROM demo.metrics WHERE $__timeFilter(ts) GROUP BY host ORDER BY host", 1),
                 {"orientation": "horizontal", "displayMode": "gradient", "reduceOptions": {"calcs": ["lastNotNull"], "values": True, "fields": "/^max_cpu$/"}},
                 {"defaults": {"unit": "percent", "min": 0, "max": 100}, "overrides": []})


def p_pie_ch():
    return panel("piechart", "Requests share (ClickHouse)", CH,
                 chq("SELECT host, sum(rps) AS requests FROM demo.metrics WHERE $__timeFilter(ts) GROUP BY host", 1),
                 {"reduceOptions": {"calcs": ["lastNotNull"], "values": True, "fields": "/^requests$/"}, "pieType": "donut", "legend": {"displayMode": "table", "placement": "right", "values": ["percent"]}})


def p_prom_req():
    return panel("timeseries", "Prometheus HTTP requests/s by handler", PROM,
                 [promq("sum by (handler) (rate(prometheus_http_requests_total[1m]))", "{{handler}}")],
                 {"legend": {"displayMode": "table", "placement": "right", "calcs": ["lastNotNull"]}},
                 {"defaults": {"unit": "reqps", "custom": {"lineWidth": 2, "fillOpacity": 10}}, "overrides": []})


def p_prom_mem():
    return panel("timeseries", "Resident memory by job (Prometheus)", PROM,
                 [promq("process_resident_memory_bytes", "{{job}}")], {"legend": {"displayMode": "list", "placement": "bottom"}},
                 {"defaults": {"unit": "bytes", "custom": {"lineWidth": 2, "fillOpacity": 10}}, "overrides": []})


def p_prom_up():
    return panel("stat", "Targets up", PROM, [promq("sum(up)", "up")],
                 {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "background"},
                 {"defaults": {"thresholds": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 3}]}}, "overrides": []})


def p_prom_series():
    return panel("stat", "TSDB head series", PROM, [promq("prometheus_tsdb_head_series", "series")],
                 {"reduceOptions": {"calcs": ["lastNotNull"]}, "graphMode": "area"},
                 {"defaults": {"thresholds": {"mode": "absolute", "steps": [{"color": "blue", "value": None}]}}, "overrides": []})


def p_prom_goroutines():
    return panel("timeseries", "Goroutines (Prometheus)", PROM, [promq("go_goroutines", "{{job}}")],
                 {"legend": {"displayMode": "list", "placement": "bottom"}},
                 {"defaults": {"custom": {"lineWidth": 2, "fillOpacity": 8}}, "overrides": []})


def p_ch_queries():
    return panel("timeseries", "ClickHouse queries/s (scraped via Prometheus)", PROM,
                 [promq("rate(ClickHouseProfileEvents_Query[1m])", "queries/s")],
                 {"legend": {"displayMode": "list", "placement": "bottom"}},
                 {"defaults": {"custom": {"lineWidth": 2, "fillOpacity": 10}}, "overrides": []})


def p_inf_up():
    t = {"refId": "A", "datasource": INF, "type": "json", "source": "url", "format": "table", "parser": "backend",
         "url": "http://prometheus:9090/api/v1/targets", "root_selector": "data.activeTargets",
         "url_options": {"method": "GET", "data": "", "params": [], "headers": []},
         "columns": [{"selector": "labels.job", "text": "job", "type": "string"},
                     {"selector": "lastScrapeDuration", "text": "scrape_s", "type": "number"}]}
    return panel("bargauge", "Scrape duration by job (Infinity)", INF, [t],
                 {"orientation": "horizontal", "displayMode": "gradient",
                  "reduceOptions": {"calcs": ["lastNotNull"], "values": True, "fields": "/^scrape_s$/"}},
                 {"defaults": {"unit": "s", "decimals": 4, "min": 0}, "overrides": []})


# ---- dashboards --------------------------------------------------------------------------------
def dashboard(uid, title, panels, variables=False, cols=2, h=9, tags=None, since="now-6h"):
    pls = []
    for i, p in enumerate(panels):
        p = copy.deepcopy(p)
        p["id"] = i + 1
        p["gridPos"] = {"x": (i % cols) * (24 // cols), "y": (i // cols) * h, "w": 24 // cols, "h": h}
        pls.append(p)
    d = {"uid": uid, "title": title, "schemaVersion": 41, "version": 1, "refresh": "30s", "tags": ["demo"] + (tags or []),
         "time": {"from": since, "to": "now"}, "panels": pls,
         "templating": {"list": []}}
    if variables:
        d["templating"]["list"].append({"name": "host", "type": "custom", "query": HOSTS, "label": "host",
                                        "current": {"text": "web", "value": "web"},
                                        "options": [{"text": h_, "value": h_, "selected": h_ == "web"} for h_ in HOSTS.split(",")]})
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.json"):
        f.unlink()
    boards = {
        "00-overview": dashboard("overview", "00 Overview (all plugins)", [
            p_stat_ch(), p_prom_up(), p_ts_ch("cpu"), p_prom_req(), p_table_ch(), p_charts(), p_text(), p_calendar(),
            p_graphviz_code(), p_table_inf()], cols=2, h=9, since="now-1h"),
        "01-business-table": dashboard("business-table", "01 Business Table", [p_table_ch(), p_table_inf()], h=14),
        "02-business-charts": dashboard("business-charts", "02 Business Charts", [p_charts(), p_ts_ch("cpu", "Same data as a native time series")], h=14),
        "03-business-text": dashboard("business-text", "03 Business Text", [p_text(), p_bar_ch()], h=12),
        "04-business-calendar": dashboard("business-calendar", "04 Business Calendar", [p_calendar()], cols=1, h=20),
        "05-business-variable": dashboard("business-variable", "05 Business Variable", [p_variable(), p_ts_ch("cpu", "CPU of the selected host", True)], variables=True, h=12),
        "06-graphviz": dashboard("graphviz", "06 Graphviz", [p_graphviz_code(), p_graphviz_query()], h=14),
        "07-clickhouse": dashboard("clickhouse", "07 ClickHouse", [p_stat_ch(), p_pie_ch(), p_ts_ch("cpu"), p_ts_ch("mem"), p_ts_ch("rps"), p_bar_ch(), p_ch_queries()], h=8),
        "08-prometheus": dashboard("prometheus", "08 Prometheus", [p_prom_up(), p_prom_series(), p_prom_req(), p_prom_mem(), p_prom_goroutines(), p_ch_queries()], h=8, since="now-30m"),
        "09-infinity": dashboard("infinity", "09 Infinity", [p_table_inf(), p_inf_up()], h=12),
    }
    for name, d in boards.items():
        (OUT / f"{name}.json").write_text(json.dumps(d, indent=1))
    print("wrote", len(boards), "dashboards")


if __name__ == "__main__":
    main()
