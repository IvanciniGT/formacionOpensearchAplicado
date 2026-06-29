# Dashboard complementario — `Iván · Incidentes, Geo y Salud`

Diseño de un segundo dashboard que **añade los componentes que faltan** en "Dashboard General Iván"
y que **revela los 3 incidentes** del dataset `streaming-events-ivan`.

Tu dashboard actual usa: Metric, Pie, Horizontal Bar, Table, Area, Tag Cloud, Markdown.
Este usa **tipos nuevos**: Gauge, Heat Map, Maps (geo), Region Map, TSVB, Vertical Bar apilada, Goal.

> Formato de cada panel: **tipo · métrica (Y) · cubo (X/split) · campo · filtro**.
> Recuerda prefijar todo con tu nombre (`Ivan_...`).

---

## Paneles propuestos

### Fila 1 — KPIs con semáforo (Gauge / Goal / Metric)

| Panel | Tipo | Métrica | Campo / config | Para qué |
|---|---|---|---|---|
| `Ivan_Error_Rate_Gauge` | **Gauge** | `Average` | `is_error` · rangos 0–0.05 verde, 0.05–0.12 ámbar, >0.12 rojo | error rate con semáforo |
| `Ivan_CacheHit_Gauge` | **Gauge** | `Average` | `cache_hit` · 0–0.6 rojo, 0.6–0.8 ámbar, >0.8 verde | salud de CDN |
| `Ivan_p99_Latencia` | **Metric** | `Percentiles` (99) | `latency_ms` · umbral color >2000 rojo | cola de latencia |
| `Ivan_Usuarios_Unicos` | **Metric** | `Unique Count` | `user_id` | audiencia real |

> El **Gauge** es justo lo que te falta: convierte un ratio (error rate, cache hit) en un semáforo
> con umbrales. El truco del ratio: `Average` sobre un booleano da la proporción de `true`.

### Fila 2 — Heat Map (mapa de calor matricial)

| Panel | Tipo | Métrica | Cubo | Para qué |
|---|---|---|---|---|
| `Ivan_HeatMap_Status_Servicio` | **Heat Map** | `Count` | X: Terms `service` · Y: Terms `status_code` | **revela incidentes 1 y 3** |
| `Ivan_HeatMap_Hora_Dia` | **Heat Map** | `Count` | X: Date Histogram `@timestamp` (1h) · Y: Terms `device_type` | patrón de uso por dispositivo/hora |

> En `HeatMap_Status_Servicio` se enciende la celda **cdn-edge × 504** (incidente CDN) y
> **recommendation-api × 503** (incidente reco). Es la visualización más potente para "ver" qué
> servicio falla y con qué código, todo a la vez.

### Fila 3 — Geoposicionamiento (mapas)

| Panel | Tipo | Métrica | Cubo | Para qué |
|---|---|---|---|---|
| `Ivan_Mapa_Errores` | **Maps** (capa heatmap o cluster) | `Count` | Geohash sobre `geo.location` · filtro `is_error: true` | **revela incidente CDN (Madrid/Barcelona)** |
| `Ivan_Mapa_Eventos` | **Maps** (cluster) | `Count` | Geohash sobre `geo.location` | dónde están los usuarios |
| `Ivan_RegionMap_Pais` | **Region Map** (coroplético) | `Count` | Terms `country_code` | tráfico por país (mapa de países coloreado) |

> Dos mapas distintos: **Maps** usa el `geo_point` real (puntos/calor sobre el globo);
> **Region Map** colorea países enteros por volumen (`country_code`). Buen contraste didáctico.

### Fila 4 — Series temporales avanzadas (TSVB) — revela el incidente Smart TV

| Panel | Tipo | Métrica | Cubo | Para qué |
|---|---|---|---|---|
| `Ivan_TSVB_Latencia_p95_Device` | **TSVB** | `Percentiles` (95) `latency_ms` | Date Histogram + **Group by Terms `device_type`** | **revela incidente Smart TV** (una línea se dispara) |
| `Ivan_Status_Apilado_Hora` | **Vertical Bar apilada** | `Count` | Date Histogram (1h) + split Terms `status_code` | picos de 504/503 en el tiempo |

> **TSVB** (Time Series Visual Builder) es el salto de nivel respecto al Area simple: permite varias
> series por `device_type` en el mismo gráfico, medias móviles, etc. La línea de **Smart TV** se
> separa claramente del resto durante el incidente de hace ~6 días.

### Fila 5 — Detalle accionable

| Panel | Tipo | Métrica | Cubo | Para qué |
|---|---|---|---|---|
| `Ivan_Endpoints_Lentos` | **Data Table** | `Average` `latency_ms` (orden desc) | Terms `api_endpoint` | qué endpoint penaliza |
| `Ivan_Markdown_Guion` | **Markdown** | — | — | guion: "pincha cada pico para investigar" |

---

## Otros componentes "distintos" que podrías meter

Si quieres enseñar aún más variedad de tipos:

- **Goal** — hermano del Gauge pero como barra de progreso hacia un objetivo (p.ej. "uptime objetivo
  95% de eventos sin error"). Visualmente distinto al Gauge circular.
- **Timelion** — series temporales por **expresión** (`.es(...)`), permite cosas como
  "errores de hoy vs. misma hora de ayer" o derivadas. Muy vistoso para comparar periodos.
- **Vega / Vega-Lite** — visualización **totalmente custom** (scatter latencia vs. bytes, etc.).
  Es el "modo experto"; ideal para enseñar que cuando los tipos estándar no llegan, hay Vega.
- **Controls** — no es un gráfico, es un panel de **filtros interactivos** (desplegables de
  `service`, `city`, `device_type`, `level`…). Convierte el dashboard en una herramienta de
  investigación: filtras y todo reacciona.
- **Coordinate Map** (alternativa clásica a Maps) — círculos proporcionales sobre el mapa por
  `geohash_grid`, más simple de configurar que Maps.

---

## Cobertura de incidentes (para la demo)

| Incidente | Panel que lo delata |
|---|---|
| CDN timeout (Madrid/Barcelona, 504) | `Ivan_Mapa_Errores` + `Ivan_HeatMap_Status_Servicio` (cdn-edge×504) |
| Latencia Smart TV | `Ivan_TSVB_Latencia_p95_Device` (línea Smart TV) |
| Recommendation API 503 | `Ivan_HeatMap_Status_Servicio` (reco×503) + `Ivan_Status_Apilado_Hora` |

> Con un panel **Controls** arriba, filtras por `service` o `city` y los 14+ paneles reaccionan a la
> vez: ese es el momento "ajá" de la clase sobre investigación de incidencias.
