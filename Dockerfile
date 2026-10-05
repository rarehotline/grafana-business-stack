FROM docker.io/grafana/grafana-oss:13.0.2

# Plugins are built from GitHub sources (build-plugin.sh) and unpacked into plugins/ (install-plugins.sh).
COPY --chown=472:0 plugins/ /var/lib/grafana/plugins/

# Our own builds are not signed by Grafana, so allow-list them explicitly.
ENV GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=grafana-clickhouse-datasource,grafana-llm-app,marcusolsson-calendar-panel,grafana-graphviz-panel,yesoreyeram-infinity-datasource,marcusolsson-dynamictext-panel,marcusolsson-static-datasource,volkovlabs-echarts-panel,volkovlabs-table-panel,volkovlabs-variable-panel \
    GF_PLUGINS_PREINSTALL_DISABLED=true \
    GF_PLUGINS_PLUGIN_ADMIN_ENABLED=false \
    GF_ANALYTICS_CHECK_FOR_UPDATES=false \
    GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES=false \
    GF_ANALYTICS_REPORTING_ENABLED=false \
    GF_NEWS_NEWS_FEED_ENABLED=false

# Keep Grafana's data (sqlite, sessions) out of /var/lib/grafana, which also holds the baked-in plugins:
# mounting a volume over that path would hide the plugins.
USER root
RUN mkdir -p /var/lib/grafana-data && chown 472:0 /var/lib/grafana-data && chmod 775 /var/lib/grafana-data
USER 472
ENV GF_PATHS_DATA=/var/lib/grafana-data
VOLUME /var/lib/grafana-data
