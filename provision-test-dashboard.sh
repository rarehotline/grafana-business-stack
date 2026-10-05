#!/usr/bin/env bash
# Creates a smoke-test dashboard with one panel per self-built plugin (TestData datasource).
set -euo pipefail
G=${GRAFANA_URL:-http://localhost:3000}; A=${GRAFANA_AUTH:-admin:admin}
curl -sf -u "$A" -X POST "$G/api/datasources" -H 'Content-Type: application/json' \
  -d '{"name":"TestData","type":"grafana-testdata-datasource","access":"proxy","isDefault":true}' >/dev/null || true
panel() { # id type title x y
  cat <<P
{"id":$1,"type":"$2","title":"$3","gridPos":{"x":$4,"y":$5,"w":12,"h":9},
 "datasource":{"type":"grafana-testdata-datasource"},
 "targets":[{"refId":"A","scenarioId":"random_walk","seriesCount":2,"datasource":{"type":"grafana-testdata-datasource"}}]
 $6}
P
}
body=$(cat <<J
{"dashboard":{"title":"Plugin smoke test","uid":"plugin-smoke","schemaVersion":41,"panels":[
$(panel 1 volkovlabs-echarts-panel "Business Charts" 0 0 ',"options":{"getOption":"return { xAxis:{type:\"category\",data:[\"a\",\"b\",\"c\"]}, yAxis:{type:\"value\"}, series:[{type:\"bar\",data:[3,7,5]}] };"}'),
$(panel 2 marcusolsson-dynamictext-panel "Business Text" 12 0 ',"options":{"content":"# Hello from Business Text\n\nRows: {{data.0.length}}","contentPartials":[],"defaultContent":"nothing","editors":[],"editor":{"language":"markdown"},"helpers":"","renderMode":"allRows","styles":""}'),
$(panel 3 volkovlabs-table-panel "Business Table" 0 9 ''),
$(panel 4 volkovlabs-form-panel "Business Forms" 12 9 ''),
$(panel 5 volkovlabs-variable-panel "Business Variable" 0 18 '')
]},"overwrite":true}
J
)
curl -sf -u "$A" -X POST "$G/api/dashboards/db" -H 'Content-Type: application/json' -d "$body"; echo
