# grafana-business-stack

Self-hosted Grafana 13.0.2 with business plugins built from GitHub sources (nothing is fetched from grafana.com).
Ready-made image: see the Releases page.

| Plugin | Version |
|---|---|
| grafana-clickhouse-datasource | 4.22.0 |
| yesoreyeram-infinity-datasource | 4.0.0 |
| grafana-graphviz-panel (private preview) | 0.0.7 |
| marcusolsson-calendar-panel (Business Calendar) | 4.1.0 |
| marcusolsson-dynamictext-panel (Business Text) | 6.3.0 |
| volkovlabs-table-panel (Business Table) | 3.5.0 |
| volkovlabs-echarts-panel (Business Charts) | 7.1.0 |
| volkovlabs-variable-panel (Business Variable) | 5.0.0 |
| marcusolsson-static-datasource | 5.1.0 |

The plugins are not signed by Grafana; the image allow-lists them via `GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS`.

## Run the prebuilt image (podman)

```bash
gunzip -c grafana-business-13.0.2.tar.gz | podman load
podman run -d --name grafana -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=change-me \
  -v grafana-data:/var/lib/grafana \
  -v /srv/data:/data:ro,Z \
  localhost/grafana-business:13.0.2
```

`:Z` relabels the bind mount for SELinux (RHEL).

## Build it yourself

Needs git, go, zip, mise (for Node 24), podman. x86_64 only (the Go backends are built for linux/amd64).

```bash
./build-plugin.sh grafana/clickhouse-datasource v4.22.0 clickhouse
./build-plugin.sh grafana/grafana-infinity-datasource v4.0.0 infinity
./build-plugin.sh grafana/grafana-graphviz-panel v0.0.7 graphviz
./build-plugin.sh VolkovLabs/business-calendar v4.1.0 business-calendar
./build-plugin.sh grafana/business-text v6.3.0 business-text
./build-plugin.sh VolkovLabs/business-table v3.5.0 business-table
./build-plugin.sh VolkovLabs/business-charts v7.1.0 business-charts
./build-plugin.sh VolkovLabs/business-variable v5.0.0 business-variable
./build-plugin.sh marcusolsson/grafana-static-datasource v5.1.0 static-datasource
./install-plugins.sh
podman build -t grafana-business:13.0.2 .
```

`docker-compose.yaml` runs the same plugins from `./plugins` plus the demo dashboards in `provisioning/` (default login admin/admin, local testing only).
