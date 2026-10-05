-- Views relative to now(), so the demo data never goes stale.
CREATE VIEW IF NOT EXISTS demo.metrics AS
SELECT toDateTime(now() - number * 60) AS ts, host,
       round(greatest(1, least(99, 45 + 25 * sin(number / 11 + cityHash64(host) % 7) + (cityHash64(number, host) % 100) / 8)), 1) AS cpu,
       round(greatest(1, least(99, 60 + 15 * sin(number / 23 + cityHash64(host) % 5) + (cityHash64(host, number) % 100) / 15)), 1) AS mem,
       toUInt32(50 + 40 * (1 + sin(number / 7 + cityHash64(host) % 3)) + cityHash64(number) % 30) AS rps
FROM numbers(1440) ARRAY JOIN ['web', 'api', 'db'] AS host;

CREATE VIEW IF NOT EXISTS demo.events AS
SELECT t.1 AS title, toDateTime(now() + t.2 * 3600) AS start, toDateTime(now() + (t.2 + t.3) * 3600) AS end, t.4 AS kind
FROM (SELECT arrayJoin([
  ('Deploy web', -70, 1, 'deploy'), ('DB maintenance', -50, 3, 'maintenance'), ('Release 1.4', -26, 2, 'release'),
  ('Incident api', -8, 2, 'incident'), ('Deploy api', 3, 1, 'deploy'), ('Backup window', 10, 4, 'maintenance'),
  ('Release 1.5', 30, 2, 'release'), ('Load test', 52, 5, 'test')]) AS t);

CREATE VIEW IF NOT EXISTS demo.graph AS
SELECT 'digraph G { rankdir=LR; node [shape=box style=rounded]; client -> web -> api -> db; api -> cache; web -> cdn; }' AS dot;
