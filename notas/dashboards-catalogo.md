# Catálogo de dashboards — `streaming-events-ivan`

Dashboards concretos que puedes construir con este dataset, panel a panel.
Para cada panel se indica: **tipo de visualización · métrica (Y) · cubo (X/split) · campo · filtro**.

> **Cómo leer cada recipe:**
> - **Métrica** = qué número se calcula (eje Y): `Count`, `Average`, `Sum`, `Max`, `Unique count`, `Percentiles`.
> - **Cubo** = cómo se agrupa (eje X o "split"): `Date Histogram`, `Terms`, `Filters`.
> - **Filtro** = condición que acota el panel (se pone en el propio panel o como filtro global).
>
> En Dashboards 3.x: **Visualize → Create**. Para KPIs usa *Metric*; series *TSVB* o *Line*;
> rankings *Vertical/Horizontal Bar* o *Data Table*; reparto *Pie/Donut*; mapas *Maps*.
> Recuerda **prefijar cada visualización/dashboard con tu nombre** (`ivan - ...`).

Campos clave para tener a mano:

```text
Tiempo     : @timestamp
Métricas   : latency_ms, buffering_ms, rebuffer_count, bytes_sent, bitrate_kbps,
             cpu_client_pct, memory_client_mb, duration_ms
Booleanos  : is_error, cache_hit, is_premium
Dimensiones: service, level, status_code, error_code, event_type, environment, host,
             country, city, region, device_type, os, isp, user_plan,
             content_title.keyword, content_type, genre, cdn_provider, edge_node, api_endpoint
Geo        : geo.location
Identidad  : user_id, session_id (para "Unique count")
```

> **Truco "ratio/porcentaje":** `Average` sobre un campo booleano da la proporción de `true` (0–1).
> `Average` de `is_error` = **error rate**. `Average` de `cache_hit` = **cache hit ratio**.
> Multiplica por 100 en el formato del campo para verlo como %.

---

## Dashboard 1 — `Streaming Operations Overview`

Visión operativa de un vistazo. Es el dashboard "de pantalla grande" del NOC.

| Panel | Visualización | Métrica | Cubo | Campo / filtro |
|---|---|---|---|---|
| Total eventos | Metric | `Count` | — | — |
| Error rate | Metric | `Average` | — | `is_error` (formato %) |
| Latencia media | Metric | `Average` | — | `latency_ms` |
| p95 latency | Metric | `Percentiles` (95) | — | `latency_ms` |
| Cache hit ratio | Metric | `Average` | — | `cache_hit` (formato %) |
| Eventos por hora | Line (TSVB) | `Count` | Date Histogram 1h | `@timestamp` |
| Eventos por servicio | Vertical Bar | `Count` | Terms (size 9) | `service` |
| Eventos por tipo | Donut | `Count` | Terms (size 11) | `event_type` |
| Tráfico por dispositivo | Donut | `Count` | Terms | `device_type` |

> Demo: con `Last 14 days`, "Eventos por hora" muestra la onda día/noche; en "Eventos por servicio"
> destaca `cdn-edge` y `player-api`.

---

## Dashboard 2 — `Errores e Incidencias` (troubleshooting)

El dashboard para **investigar**. Aquí se ven los 3 incidentes.

| Panel | Visualización | Métrica | Cubo | Campo / filtro |
|---|---|---|---|---|
| Errores por hora | Line | `Count` | Date Histogram 1h | `@timestamp` · filtro `is_error: true` |
| Error rate por hora | Line (TSVB) | `Average` | Date Histogram 1h | `is_error` |
| Top error_code | Horizontal Bar | `Count` | Terms (size 12) | `error_code` |
| Top servicios con error | Horizontal Bar | `Count` | Terms (size 9) | `service` · filtro `is_error: true` |
| Status codes | Donut | `Count` | Terms | `status_code` |
| Status code por hora | Bar apilada | `Count` | Date Histogram 1h + split Terms `status_code` | `@timestamp` |
| Errores por dispositivo | Vertical Bar | `Count` | Terms | `device_type` · filtro `is_error: true` |
| Errores por ISP | Horizontal Bar | `Count` | Terms (size 12) | `isp` · filtro `is_error: true` |
| Últimos errores | Data Table / Saved Search | — | ordenar `@timestamp` desc | filtro `level: ERROR`; columnas: `@timestamp, service, status_code, error_code, city, device_type, latency_ms, message` |

> Demo de incidentes: pincha cada pico en "Errores por hora" →
> hace ~10 d: `CDN_TIMEOUT` + `504`; hace ~6 d: latencia (ver Dashboard 3); hace ~2 d: `503` + `recommendation-api`.

---

## Dashboard 3 — `Calidad de Experiencia (QoE)`

Cómo de bien (o mal) reproduce el usuario. El dashboard donde se ve el **incidente Smart TV**.

| Panel | Visualización | Métrica | Cubo | Campo / filtro |
|---|---|---|---|---|
| p50 / p95 / p99 latencia | Metric (×3) o Gauge | `Percentiles` (50/95/99) | — | `latency_ms` |
| Latencia p95 por hora | Line (TSVB) | `Percentiles` (95) | Date Histogram 1h | `latency_ms` |
| Latencia por dispositivo | Vertical Bar | `Percentiles` (95) o `Average` | Terms | `device_type` ← **Smart TV destaca** |
| Latencia media por servicio | Horizontal Bar | `Average` | Terms (size 9) | `service` |
| Buffering medio por dispositivo | Vertical Bar | `Average` | Terms | `device_type` · campo `buffering_ms` |
| Rebuffer count por dispositivo | Vertical Bar | `Sum` o `Average` | Terms | `device_type` · campo `rebuffer_count` |
| Endpoints más lentos | Data Table | `Average` `latency_ms` (orden desc) | Terms (size 15) | `api_endpoint` |
| CPU/memoria cliente | Data Table | `Average` `cpu_client_pct`, `Average` `memory_client_mb` | Terms | `device_type` |

> Demo: "Latencia por dispositivo" con `Percentiles 95` muestra Smart TV ~7.000 ms frente a ~3.500
> del resto. Acota al pico de hace ~6 días y se dispara aún más.

---

## Dashboard 4 — `Geografía y CDN`

Dónde están los usuarios y cómo rinde la red. Aquí se ve el **incidente CDN geográfico**.

| Panel | Visualización | Métrica | Cubo | Campo / filtro |
|---|---|---|---|---|
| Mapa de eventos | Maps (cluster / heatmap) | `Count` | Geohash sobre `geo.location` | — |
| Mapa de errores | Maps (heatmap) | `Count` | Geohash sobre `geo.location` | filtro `is_error: true` |
| Top ciudades | Horizontal Bar | `Count` | Terms (size 16) | `city` |
| Error rate por ciudad | Data Table | `Average` `is_error` (orden desc) | Terms (size 16) | `city` (formato %) |
| Eventos por país | Region Map / Donut | `Count` | Terms | `country` (o `country_code`) |
| Cache hit por proveedor CDN | Vertical Bar | `Average` `cache_hit` | Terms | `cdn_provider` (formato %) |
| Latencia media por ciudad | Data Table | `Average` `latency_ms` | Terms (size 16) | `city` |
| Top edge nodes con error | Horizontal Bar | `Count` | Terms (size 15) | `edge_node` · filtro `is_error: true` |

> Demo: en "Mapa de errores" y "Error rate por ciudad", Madrid y Barcelona se encienden durante
> el incidente CDN (hace ~10 d). Sin filtro temporal, el error rate está más repartido.

---

## Dashboard 5 — `Contenido y Audiencia` (negocio)

Qué se consume, cuánto tráfico genera y qué contenido da problemas.

| Panel | Visualización | Métrica | Cubo | Campo / filtro |
|---|---|---|---|---|
| Top contenidos (reproducciones) | Horizontal Bar | `Count` | Terms (size 15) | `content_title.keyword` · filtro `event_type: playback_start` |
| Top contenidos con error | Horizontal Bar | `Count` | Terms (size 10) | `content_title.keyword` · filtro `is_error: true` |
| Bytes enviados por género | Vertical Bar | `Sum` | Terms | `genre` · campo `bytes_sent` |
| Reparto por content_type | Donut | `Count` | Terms | `content_type` |
| Eventos por género | Vertical Bar | `Count` | Terms | `genre` |
| Usuarios únicos por plan | Vertical Bar | `Unique count` | Terms | `user_plan` · campo `user_id` |
| Premium vs no premium | Donut | `Count` | Terms | `is_premium` |
| Bitrate medio por dispositivo | Vertical Bar | `Average` | Terms | `device_type` · campo `bitrate_kbps` |

> Nota: usa **`content_title.keyword`** (no `content_title`) para agrupar — el `text` no agrega bien.
> "Usuarios únicos" usa `Unique count` (cardinalidad) sobre `user_id`.

---

## Dashboard 6 — `Salud de Servicios / SRE`

Orientado a plataforma: qué servicio/host falla y cómo.

| Panel | Visualización | Métrica | Cubo | Campo / filtro |
|---|---|---|---|---|
| Error rate por servicio | Horizontal Bar | `Average` `is_error` (orden desc) | Terms (size 9) | `service` (formato %) |
| Status code por servicio | Heat Map | `Count` | X: Terms `service` · Y: Terms `status_code` | — |
| Errores por host | Data Table | `Count` | Terms (size 30) | `host` · filtro `is_error: true` |
| Tráfico por entorno | Donut | `Count` | Terms | `environment` |
| Latencia p99 por servicio | Horizontal Bar | `Percentiles` (99) | Terms | `service` · campo `latency_ms` |
| Versión de app en uso | Donut | `Count` | Terms | `app_version` |
| Eventos por servicio y hora | Bar apilada | `Count` | Date Histogram 1h + split `service` | `@timestamp` |
| Recommendation API 503 | Metric | `Count` | — | filtros `service: recommendation-api` + `status_code: 503` |

> Demo: "Recommendation API 503" se dispara en el pico de hace ~2 días (incidente 3).

---

## Filtros globales (Controls) recomendados

Añade un panel **Controls** (Dropdown) al dashboard para que la audiencia filtre en vivo:

```text
time picker (siempre)   country     city        service
level                   device_type user_plan   genre
isp                     cache_hit    status_code error_code
```

Con esos controles, **un solo dashboard** sirve para investigar cualquier incidente: filtras por
servicio o ciudad y todos los paneles reaccionan a la vez.

---

## Resumen: qué tipo de visualización para qué

| Quiero mostrar... | Visualización | Pista |
|---|---|---|
| Un número clave (KPI) | **Metric** / Gauge | `Count`, `Average`, `Percentiles` sin cubo |
| Evolución en el tiempo | **Line** / Area / TSVB | cubo `Date Histogram` sobre `@timestamp` |
| Ranking / top N | **Horizontal Bar** / Data Table | cubo `Terms` ordenado por la métrica |
| Reparto / proporción | **Pie / Donut** | cubo `Terms` con pocos valores |
| Comparar 2 dimensiones | **Heat Map** / Bar apilada | dos `Terms` (X e Y / split) |
| Distribución geográfica | **Maps** / Region Map | `geo.location` (geohash) o `country` |
| Listado de eventos crudos | **Data Table** / Saved Search | sin agregación, ordenar por `@timestamp` |
| Ratio (%) | cualquiera | `Average` de un booleano (`is_error`, `cache_hit`) |
