# Lab — Streaming / CDN / Observabilidad de reproducción

Laboratorio completo para **OpenSearch 3.6.0 + OpenSearch Dashboards**, orientado a enseñar
Discover, Visualizations, Dashboards, mapas geográficos, KPIs, series temporales, rankings,
filtros interactivos, agregaciones, percentiles e investigación de incidencias.

**Índice:** `streaming-events-ivan`
**Caso:** plataforma de streaming con eventos de reproducción, errores, latencias, tráfico por
ciudad, dispositivos, servicios, ISPs y contenidos.

> **Índice compartido — toda la clase usa el mismo `streaming-events-ivan`.** El lab es de
> **solo lectura** (Discover, visualizaciones, dashboards y agregaciones no modifican datos), así
> que no hay práctica de ingest: el índice lo carga el formador **una sola vez** (apartados 1–5,
> ya hechos). Los alumnos **empiezan en el apartado 6**.
> - Cada alumno crea su **data view** contra `streaming-events-ivan*` y monta **sus** dashboards.
> - **Prefija tus visualizaciones y dashboards con tu nombre** (p.ej. `ivan - Streaming Overview`)
>   para que no choquen con los de los demás.
> - ⚠️ **Nadie escribe ni borra el índice**, solo se consulta. El `DELETE` del final es solo para
>   el formador.

> **Cómo ejecutar:** los bloques `GET` de consulta son **Dev Tools**
> (OpenSearch Dashboards → ☰ → Dev Tools). Los apartados 1–5 (mapping/carga) son tarea del formador.

---

## Índice del lab

1. [Mapping del índice (Dev Tools)](#1-mapping-del-índice-dev-tools)
2. [Script Python de generación](#2-script-python-de-generación)
3. [Generar los datos](#3-generar-los-datos)
4. [Cargar el bulk](#4-cargar-el-bulk)
5. [Refrescar y comprobar](#5-refrescar-y-comprobar)
6. [Queries de prueba](#6-queries-de-prueba)
7. [Agregaciones para dashboards](#7-agregaciones-para-dashboards)
8. [Data View en Dashboards](#8-data-view-en-dashboards)
9. [Visualizaciones recomendadas](#9-visualizaciones-recomendadas)
10. [Dashboard: Streaming Operations Overview](#10-dashboard-streaming-operations-overview)
11. [Qué patrón de datos se ha simulado](#11-qué-patrón-de-datos-se-ha-simulado)

---

## 1. Mapping del índice (Dev Tools)

`status_code` se modela como **`keyword`** (no number): nunca hacemos aritmética con él, pero sí
rankings y filtros (`terms`, `term`). Todos los campos de agregación/filtro son `keyword`; las
métricas numéricas son `integer`/`long`/`float`; `geo.location` es `geo_point` para mapas.

```
PUT streaming-events-ivan
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "@timestamp":       { "type": "date" },

      "event_id":         { "type": "keyword" },
      "event_type":       { "type": "keyword" },
      "service":          { "type": "keyword" },
      "environment":      { "type": "keyword" },
      "host":             { "type": "keyword" },
      "level":            { "type": "keyword" },
      "status_code":      { "type": "keyword" },
      "country":          { "type": "keyword" },
      "country_code":     { "type": "keyword" },
      "region":           { "type": "keyword" },
      "city":             { "type": "keyword" },
      "device_type":      { "type": "keyword" },
      "os":               { "type": "keyword" },
      "app_version":      { "type": "keyword" },
      "user_plan":        { "type": "keyword" },
      "isp":              { "type": "keyword" },
      "content_id":       { "type": "keyword" },
      "content_type":     { "type": "keyword" },
      "genre":            { "type": "keyword" },
      "error_code":       { "type": "keyword" },
      "cdn_provider":     { "type": "keyword" },
      "edge_node":        { "type": "keyword" },
      "request_method":   { "type": "keyword" },
      "api_endpoint":     { "type": "keyword" },
      "session_id":       { "type": "keyword" },
      "user_id":          { "type": "keyword" },

      "geo": {
        "properties": {
          "location":     { "type": "geo_point" }
        }
      },

      "latency_ms":       { "type": "integer" },
      "duration_ms":      { "type": "integer" },
      "bytes_sent":       { "type": "long" },
      "bitrate_kbps":     { "type": "integer" },
      "buffering_ms":     { "type": "integer" },
      "rebuffer_count":   { "type": "integer" },
      "cpu_client_pct":   { "type": "float" },
      "memory_client_mb": { "type": "integer" },

      "cache_hit":        { "type": "boolean" },
      "is_error":         { "type": "boolean" },
      "is_premium":       { "type": "boolean" },

      "content_title": {
        "type": "text",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "message":          { "type": "text" },
      "user_agent":       { "type": "text" }
    }
  }
}
```

> **Truco para la carga masiva:** si vas a indexar los 100k de golpe, crea el índice con
> `"refresh_interval": "-1"` en `settings`, carga, y luego vuelve a ponerlo en `"1s"`. Acelera mucho.
> ```
> PUT streaming-events-ivan/_settings
> { "index": { "refresh_interval": "1s" } }
> ```

---

## 2. Script Python de generación

El script completo está en **[`generate_streaming_events.py`](generate_streaming_events.py)**
(misma carpeta). Sin dependencias externas (solo librería estándar de Python 3).

Qué hace:

- Genera N documentos NDJSON listos para `_bulk` (línea de acción + línea de documento).
- Distribución temporal **no uniforme**: pico 19:00–23:30 UTC, valle 02:00–07:00, y más tráfico
  viernes/sábado/domingo.
- **Reglas de coherencia** (validadas): `INFO` nunca lleva `error_code`; `ERROR` siempre lo lleva;
  `is_error = (level==ERROR or status>=500)`; Smart TV solo Tizen/webOS, Mobile solo Android/iOS, etc.
- Inyecta los **3 incidentes** obligatorios (ver §11).
- Seed fija (`--seed 42`) → reproducible.

Parámetros:

```
--docs    nº de documentos        (def. 100000)
--index   nombre del índice        (def. streaming-events-ivan)
--output  fichero NDJSON de salida (def. streaming-events.bulk.ndjson)
--seed    semilla                  (def. 42)
```

---

## 3. Generar los datos

```bash
python3 generate_streaming_events.py \
  --docs 100000 \
  --index streaming-events-ivan \
  --output streaming-events.bulk.ndjson
```

Salida esperada (resumen):

```
Documentos generados : 100,000
  - base             : 91,500
  - incidente 1 (CDN) : 3,000   [hace ~10 días, 2 h]
  - incidente 2 (TV)  : 4,000   [hace ~6 días, 4 h]
  - incidente 3 (reco): 1,500   [hace ~2 días, 45 min]
Fichero  : .../streaming-events.bulk.ndjson  (~107 MB)
```

> Para una demo rápida en clase puedes generar menos: `--docs 20000`.

---

## 4. Cargar el bulk

### Opción A — `curl` desde terminal (recomendado para 100k)

El fichero pesa ~107 MB. Conviene **trocearlo** para no mandar todo en una sola petición
(`_bulk` carga el cuerpo entero en memoria). Cada doc son 2 líneas, así que 20.000 líneas = 10.000 docs:

```bash
# 1) trocear en ficheros de 10.000 docs
split -l 20000 streaming-events.bulk.ndjson part_

# 2) cargar cada trozo
for p in part_*; do
  curl -sk -u admin:'Pa$$w0rd2026' \
    -H 'Content-Type: application/x-ndjson' \
    -X POST "https://opensearch.iochannel.tech/_bulk" \
    --data-binary @"$p" \
    -o /dev/null -w "$p -> %{http_code}\n"
done

# 3) limpiar
rm -f part_*
```

Si tu fichero es pequeño (`--docs 20000` o menos), puedes cargarlo de una:

```bash
curl -sk -u admin:'Pa$$w0rd2026' \
  -H 'Content-Type: application/x-ndjson' \
  -X POST "https://opensearch.iochannel.tech/_bulk" \
  --data-binary @streaming-events.bulk.ndjson | python3 -c "import sys,json;d=json.load(sys.stdin);print('errors:',d['errors'])"
```

> ⚠️ Usa `--data-binary` (no `-d`): `-d` se come los saltos de línea y rompe el NDJSON.

### Opción B — Dev Tools

Dev Tools **no sirve para cargar el fichero completo** (no lee de disco y 100k peticiones lo
cuelgan). Úsalo solo para pegar **un par de documentos de ejemplo** y enseñar el formato `_bulk`:

```
POST _bulk
{ "index": { "_index": "streaming-events-ivan" } }
{ "@timestamp": "2026-06-25T20:13:45.123Z", "event_type": "segment_request", "service": "cdn-edge", "level": "INFO", "status_code": "200", "city": "Madrid", "geo": { "location": { "lat": 40.4168, "lon": -3.7038 } }, "device_type": "Smart TV", "os": "Tizen", "latency_ms": 120, "cache_hit": true, "is_error": false, "message": "Segment delivered from CDN cache" }

```

---

## 5. Refrescar y comprobar

```
POST streaming-events-ivan/_refresh
```

```
GET streaming-events-ivan/_count
```
→ `"count": 100000`

```
GET _cat/indices/streaming-events-ivan?v
```

```
GET _cat/shards/streaming-events-ivan?v&h=index,shard,prirep,state,docs,node
```

---

## 6. Queries de prueba

### 6.1 Últimos errores

```
GET streaming-events-ivan/_search
{
  "size": 10,
  "sort": [ { "@timestamp": "desc" } ],
  "_source": ["@timestamp","level","service","status_code","error_code","city","device_type","latency_ms","message"],
  "query": {
    "bool": {
      "filter": [
        { "term":  { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-14d" } } }
      ]
    }
  }
}
```

### 6.2 Errores `CDN_TIMEOUT` (incidente 1)

```
GET streaming-events-ivan/_search
{
  "size": 5,
  "query": { "term": { "error_code": "CDN_TIMEOUT" } }
}
```

### 6.3 Errores del servicio `recommendation-api` (incidente 3)

```
GET streaming-events-ivan/_search
{
  "size": 5,
  "query": {
    "bool": {
      "filter": [
        { "term": { "service": "recommendation-api" } },
        { "term": { "is_error": true } }
      ]
    }
  }
}
```

### 6.4 Latencias altas (> 2000 ms)

```
GET streaming-events-ivan/_search
{
  "size": 5,
  "sort": [ { "latency_ms": "desc" } ],
  "query": { "range": { "latency_ms": { "gt": 2000 } } }
}
```

### 6.5 Eventos de Smart TV (incidente 2)

```
GET streaming-events-ivan/_search
{
  "size": 5,
  "query": { "term": { "device_type": "Smart TV" } }
}
```

### 6.6 Madrid y Barcelona

```
GET streaming-events-ivan/_search
{
  "size": 5,
  "query": {
    "bool": {
      "filter": [ { "terms": { "city": ["Madrid","Barcelona"] } } ]
    }
  }
}
```

### 6.7 Búsqueda textual en `message`

```
GET streaming-events-ivan/_search
{
  "size": 5,
  "query": { "match": { "message": "timeout" } }
}
```

### 6.8 Filtrar por `status_code` y por `cache_hit = false`

```
GET streaming-events-ivan/_search
{
  "size": 5,
  "query": {
    "bool": {
      "filter": [
        { "term": { "status_code": "504" } },
        { "term": { "cache_hit": false } }
      ]
    }
  }
}
```

---

## 7. Agregaciones para dashboards

> Todas con `"size": 0` (no queremos documentos, solo el resumen). Para acotar al periodo,
> añade un `"query": { "range": { "@timestamp": { "gte": "now-14d" } } }`.

### 7.1 Eventos por hora (serie temporal)

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": {
    "por_hora": {
      "date_histogram": { "field": "@timestamp", "fixed_interval": "1h" }
    }
  }
}
```

### 7.2 Errores por hora

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "query": { "term": { "is_error": true } },
  "aggs": {
    "errores_hora": {
      "date_histogram": { "field": "@timestamp", "fixed_interval": "1h" }
    }
  }
}
```

### 7.3 Eventos por ciudad

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": { "por_ciudad": { "terms": { "field": "city", "size": 20 } } }
}
```

### 7.4 Errores por ciudad

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "query": { "term": { "is_error": true } },
  "aggs": { "errores_ciudad": { "terms": { "field": "city", "size": 20 } } }
}
```

### 7.5 Latencia media por servicio

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": {
    "por_servicio": {
      "terms": { "field": "service", "size": 20 },
      "aggs": { "latencia_media": { "avg": { "field": "latency_ms" } } }
    }
  }
}
```

### 7.6 Percentiles de latencia (p50/p90/p95/p99)

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": {
    "latencia_pct": {
      "percentiles": { "field": "latency_ms", "percents": [50,90,95,99] }
    }
  }
}
```

### 7.7 Cache hit ratio

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": {
    "cache": { "terms": { "field": "cache_hit" } },
    "ratio": { "avg": { "field": "cache_hit" } }
  }
}
```
> `avg` sobre un `boolean` da directamente la proporción de `true` (0–1). En este dataset ≈ **0.76**.

### 7.8 Top contenidos con errores

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "query": { "term": { "is_error": true } },
  "aggs": { "contenidos": { "terms": { "field": "content_title.keyword", "size": 10 } } }
}
```

### 7.9 Errores por ISP

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "query": { "term": { "is_error": true } },
  "aggs": { "isp": { "terms": { "field": "isp", "size": 15 } } }
}
```

### 7.10 Errores por dispositivo

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "query": { "term": { "is_error": true } },
  "aggs": { "device": { "terms": { "field": "device_type", "size": 10 } } }
}
```

### 7.11 Status codes por servicio (agregación anidada)

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": {
    "servicio": {
      "terms": { "field": "service", "size": 20 },
      "aggs": { "status": { "terms": { "field": "status_code", "size": 12 } } }
    }
  }
}
```

### 7.12 Bytes enviados por género

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": {
    "genero": {
      "terms": { "field": "genre", "size": 15 },
      "aggs": { "bytes": { "sum": { "field": "bytes_sent" } } }
    }
  }
}
```

### 7.13 Mapa: rejilla geográfica (`geohash_grid`)

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "aggs": {
    "mapa": { "geohash_grid": { "field": "geo.location", "precision": 4 } }
  }
}
```

Variante **solo errores** (mapa de calor de incidencias):

```
GET streaming-events-ivan/_search
{
  "size": 0,
  "query": { "term": { "is_error": true } },
  "aggs": {
    "mapa_errores": { "geohash_grid": { "field": "geo.location", "precision": 4 } }
  }
}
```

> Para latencia media por zona, anida una métrica dentro de cada celda:
> ```
> "aggs": { "mapa": { "geohash_grid": { "field": "geo.location", "precision": 4 },
>   "aggs": { "lat_media": { "avg": { "field": "latency_ms" } } } } }
> ```

---

## 8. Data View en Dashboards

```text
☰  →  Dashboards Management  →  Data Views (Index Patterns)  →  Create data view
   Nombre / index pattern:  streaming-events-ivan*
   Campo temporal (Time field):  @timestamp
   →  Create data view
```

> **IMPORTANTE — si Discover no muestra nada, revisa el time picker** (arriba a la derecha).
> Los datos abarcan los **últimos 14 días**: usa `Last 14 days` o `Last 30 days`.

En **Discover**:
1. Selecciona el data view `streaming-events-ivan*`.
2. Pon el rango temporal a `Last 14 days`.
3. Añade columnas (botón **+** sobre el campo): `service`, `level`, `status_code`, `city`,
   `device_type`, `latency_ms`, `message`.
4. Filtros: `level = ERROR`, `city = Madrid`. Búsqueda DQL: `error_code: "CDN_TIMEOUT"`.
5. **Guarda** la búsqueda (Save) → la reutilizarás en el dashboard.

---

## 9. Visualizaciones recomendadas

> En Dashboards 3.x: **Visualize → Create visualization**. Para series/rankings/KPIs lo más cómodo
> es el tipo **TSVB** o **Metric/Data table/Vertical bar** clásicos; para mapas, **Maps** o **Coordinate Map**.

### KPIs (tipo *Metric*)
| Visualización | Métrica |
|---|---|
| Total eventos | `count` |
| Error rate | `avg` de `is_error` (×100 para %) |
| Latencia media | `avg latency_ms` |
| p95 latency | `percentiles latency_ms` (95) |
| p99 latency | `percentiles latency_ms` (99) |
| Cache hit ratio | `avg` de `cache_hit` |
| Bytes enviados | `sum bytes_sent` |

### Series temporales (eje X = `date_histogram` `@timestamp`)
- Eventos por hora (`count`).
- Errores por hora (`count`, filtro `is_error: true`).
- Latencia p95 por hora (`percentiles latency_ms` 95).
- Status codes por hora (`count`, *split series* por `status_code`).

### Rankings (tipo *Horizontal/Vertical bar* o *Data table*, `terms` ordenado por métrica)
- Top servicios por errores (`terms service`, filtro `is_error`).
- Top ciudades por errores (`terms city`, filtro `is_error`).
- Top ISPs por errores (`terms isp`, filtro `is_error`).
- Top dispositivos por errores (`terms device_type`, filtro `is_error`).
- Top contenidos con errores (`terms content_title.keyword`, filtro `is_error`).
- Top endpoints lentos (`terms api_endpoint`, métrica `avg latency_ms`, orden desc).

### Geo (tipo *Maps*)
- Mapa de eventos por ciudad (`geohash_grid` o cluster por `geo.location`).
- Mapa de errores por ciudad (igual, filtro `is_error: true`).
- Mapa de latencia media por zona (`geohash_grid` + métrica `avg latency_ms`).

### Tablas (tipo *Data table*)
- Últimos errores (sin agregación, ordenado por `@timestamp` desc).
- Servicios: nº errores + latencia media (`terms service` + `avg latency_ms`).
- Contenidos problemáticos (`terms content_title.keyword` + filtro `is_error`).
- Ciudades con error rate alto (`terms city` + `avg is_error`).

### Distribuciones (tipo *Pie* / *Donut* / *Vertical bar*)
- Eventos por `device_type`, por `user_plan`, por `genre`.
- Distribución de `status_code`.
- Cache hit vs miss (`terms cache_hit`).

---

## 10. Dashboard: `Streaming Operations Overview`

Crea un dashboard (**Dashboard → Create → Add** las visualizaciones de §9) con estas secciones:

```text
┌─ CABECERA (KPIs) ──────────────────────────────────────────────┐
│ Total eventos │ Error rate │ Latencia media │ p95 │ Cache hit % │
├─ TRÁFICO ──────────────────────────────────────────────────────┤
│ Eventos por hora (línea)                                        │
│ Eventos por tipo (donut)      │ Eventos por servicio (barras)   │
├─ ERRORES ──────────────────────────────────────────────────────┤
│ Errores por hora (línea)                                        │
│ Top servicios c/error (barras)│ Top error_code (barras)         │
│ Status codes (donut)                                            │
├─ EXPERIENCIA DE USUARIO ───────────────────────────────────────┤
│ Latencia p95 por hora (línea) │ Latencia por dispositivo (barras)│
│ Buffering medio por device    │ Rebuffer count por device       │
├─ GEOGRAFÍA ────────────────────────────────────────────────────┤
│ Mapa de eventos │ Mapa de errores │ Top ciudades por error rate │
├─ CONTENIDO ────────────────────────────────────────────────────┤
│ Top contenidos c/error │ Bytes por género │ Errores por content_type│
├─ DETALLE OPERATIVO ────────────────────────────────────────────┤
│ Tabla: últimos errores                                          │
│   @timestamp │ level │ service │ status_code │ error_code │     │
│   city │ device_type │ latency_ms │ message                     │
└────────────────────────────────────────────────────────────────┘
```

**Filtros globales sugeridos** (barra de filtros + *Controls*): time picker, `country`, `city`,
`service`, `level`, `device_type`, `user_plan`, `genre`, `isp`, `cache_hit`.

**Guion de demo en clase (investigación de incidencias):**
1. Pon `Last 14 days`. En *Errores por hora* verás **3 picos** (días ~10, ~6 y ~2 atrás).
2. Pincha el pico de hace ~10 días → el dashboard filtra ese intervalo → mira *Top error_code*
   (`CDN_TIMEOUT`), *Top ciudades* (Madrid, Barcelona) y el *Mapa de errores* (concentrado en España).
   → **Incidente 1: CDN timeout geográfico.**
3. Pico de hace ~6 días → *Latencia por dispositivo* dispara **Smart TV** (p95/p99 altos), servicio
   `player-api`. → **Incidente 2: latencia Smart TV.**
4. Pico de hace ~2 días → *Top servicios c/error* = `recommendation-api`, status `503`,
   `SERVICE_UNAVAILABLE`. → **Incidente 3: recommendation API degradada.**

---

## 11. Qué patrón de datos se ha simulado

**Volumen y tiempo.** 100.000 eventos en los últimos 14 días (UTC, campo `@timestamp`). El tráfico
**no es uniforme**: pico de 19:00 a 23:30, valle de 02:00 a 07:00, y más volumen viernes/sábado/domingo,
con ruido aleatorio. Esto hace que las series temporales tengan forma realista (ondas día/noche).

**Distribuciones de fondo.** ~75% `INFO`, ~17% `WARN`, ~8% `ERROR`; status coherentes con el nivel
(`INFO`→2xx, `WARN`→4xx, `ERROR`→5xx); `error_code` ausente en `INFO` y presente en `WARN`/`ERROR`;
dispositivos con su SO real (Smart TV→Tizen/webOS, Mobile→Android/iOS…); un ISP (`SlowNet Telecom`)
con peor calidad para crear diferencias por ISP; cache hit global ≈ 76%.

**3 incidentes inyectados** (los picos del dashboard):

| # | Cuándo | Duración | Firma | Se ve en |
|---|---|---|---|---|
| 1 | hace ~10 d | 2 h | `cdn-edge`, `504`, `CDN_TIMEOUT`, Madrid+Barcelona, cache_hit↓ | serie de errores, mapa, ranking ciudades, ranking error_code |
| 2 | hace ~6 d | 4 h | `Smart TV`, `player-api`, `latency_ms` 2500–9000, buffering↑ | p95/p99, latencia por dispositivo, serie de latencia |
| 3 | hace ~2 d | 45 min | `recommendation-api`, `503`, `SERVICE_UNAVAILABLE` | errores por servicio, status por tiempo, tabla de errores |

**Verificado contra el clúster** (100k cargados): `CDN_TIMEOUT` → Madrid (1940) + Barcelona (1244),
servicio `cdn-edge`, status `504`; Smart TV p95≈7000 / p99≈8600 (vs ~3500 / ~6200 del resto);
`503` → `recommendation-api` (1656) con `SERVICE_UNAVAILABLE`; los 3 días de incidente son los de más
errores del periodo.

---

## Limpieza (opcional)

```
DELETE streaming-events-ivan
```
