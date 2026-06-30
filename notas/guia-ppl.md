# PPL — Piped Processing Language (guía básica con ejemplos)

**PPL** es el lenguaje de consultas "por tuberías" de OpenSearch: empiezas por una fuente de datos
y vas encadenando pasos con `|`, como en una terminal de Linux. Es más cómodo que Query DSL (JSON)
para explorar y analizar, sobre todo logs.

```text
source = <índice>  |  paso1  |  paso2  |  paso3 ...
```
Cada `|` toma el resultado del paso anterior y le aplica otra transformación.

> **Dónde se ejecuta:**
> - **Query Workbench**: ☰ → **Query Workbench** → pestaña **PPL** (lo más cómodo, con tabla de resultados).
> - **Observability → Logs / Event Analytics** (también usa PPL).
> - **Dev Tools / API:**
>   ```
>   POST _plugins/_ppl
>   { "query": "source=usuarios-ivan | head 5" }
>   ```

---

## 1. La idea: empezar por la fuente y filtrar

```
source = usuarios-ivan
```
Devuelve los documentos del índice. A partir de aquí, encadenamos.

```
source = usuarios-ivan | where edad > 30
```
`where` filtra (como el WHERE de SQL).

---

## 2. Elegir columnas y ordenar

```
source = usuarios-ivan
| where edad > 30
| fields nombre, edad, ciudad
| sort - edad
```

```text
fields   → qué columnas quiero ver
sort     → ordenar.  - edad = descendente,  + edad = ascendente
head 5   → quedarme solo con los 5 primeros (como LIMIT)
```

**Resultado real:**

| nombre | edad | ciudad |
|---|---|---|
| Pedro García Sanchez | 44 | Bilbao |
| Ana Fernández Soto | 42 | Valencia |
| Pedro Gómez Moreno | 39 | Bilbao |
| Juan Martínez Ruiz | 35 | Barcelona |

---

## 3. Resumir con `stats` (lo más potente)

`stats` es el agrupar-y-calcular (como GROUP BY). Formato: `stats <métrica> by <campo>`.

```
source = streaming-events-ivan
| where is_error = true
| stats count() as errores by service
| sort - errores
| head 5
```

**Resultado real:**

| errores | service |
|---|---|
| 4434 | cdn-edge |
| 2138 | recommendation-api |
| 1710 | player-api |
| 1040 | analytics-ingest |

Métricas que puedes usar: `count()`, `avg(campo)`, `sum(campo)`, `min()`, `max()`,
`percentile(campo, 95)`, `dc(campo)` (valores distintos).

### Varias métricas a la vez

```
source = streaming-events-ivan
| stats avg(latency_ms) as media, percentile(latency_ms, 95) as p95 by device_type
| sort - p95
```

**Resultado real** (se ve que **Smart TV** dispara la latencia):

| media | p95 | device_type |
|---|---|---|
| 1453 | 7036 | Smart TV |
| 737 | 3571 | Set-top Box |
| 710 | 3522 | Web |
| ... | ... | ... |

---

## 4. Crear columnas con `eval`

`eval` calcula un campo nuevo a partir de otros.

```
source = streaming-events-ivan
| eval lento = latency_ms > 1000
| stats count() by lento
```

**Resultado real:**

| count() | lento |
|---|---|
| 81425 | false |
| 18575 | true |

---

## 5. Atajos útiles

### `top` / `rare` → los más (o menos) frecuentes

```
source = streaming-events-ivan | top 3 city
```

| city | count |
|---|---|
| Madrid | 22832 |
| Barcelona | 16429 |
| London | 6649 |

`rare` es lo contrario (los menos frecuentes).

### `dedup` → quitar duplicados por un campo

```
source = usuarios-ivan | dedup ciudad | fields ciudad
```
Devuelve una fila por ciudad distinta.

### `rename` → renombrar columnas

```
source = usuarios-ivan | rename ciudad as poblacion | fields nombre, poblacion
```

---

## 6. Ejemplo real con logs (investigación)

Sobre el alias `logs` (postgres + tomcat + keycloak juntos):

```
source = logs
| stats count() as n by service, level
| sort - n
| head 6
```

**Resultado real:**

| n | service | level |
|---|---|---|
| 8485 | keycloak | INFO |
| 7985 | postgres | INFO |
| 7960 | tomcat | INFO |
| 1320 | tomcat | WARN |

Solo los errores de un pod concreto:

```
source = logs
| where level = "ERROR" and kubernetes.pod_name = "postgresql-0"
| fields @timestamp, message
| sort - @timestamp
| head 10
```

---

## 7. PPL vs Query DSL (lo mismo de dos formas)

| Quiero... | PPL | Query DSL |
|---|---|---|
| Filtrar | `source=i \| where edad>30` | `{ "range": { "edad": { "gt": 30 } } }` |
| Agrupar y contar | `source=i \| stats count() by ciudad` | `aggs` → `terms` |
| Media por grupo | `source=i \| stats avg(edad) by ciudad` | `terms` + `avg` anidado |

PPL es más corto y legible para explorar; Query DSL es el que va por debajo y el que necesitas
para búsquedas avanzadas, visualizaciones y alertas.

---

## 8. Chuleta rápida

```text
source = INDICE                       de dónde leo
| where condicion                     filtrar     (and / or / =, >, <, like)
| fields a, b, c                      elegir columnas
| sort - campo                        ordenar (- desc, + asc)
| head N                              limitar
| stats count() by campo              agrupar y contar
| stats avg(x), percentile(x,95) by g  métricas por grupo
| eval nuevo = expresion              crear columna
| top N campo                         más frecuentes
| dedup campo                         quitar duplicados
| rename viejo as nuevo               renombrar
```

> Ejecuta en **Query Workbench → PPL**, o por API:
> `POST _plugins/_ppl  { "query": "source=usuarios-ivan | head 5" }`

---

# Parte 2 — Características más avanzadas

Todo lo de abajo está probado contra el clúster del curso.

## 9. Series temporales con `span()`

`span(campo_fecha, intervalo)` agrupa por ventanas de tiempo (hora, día...). Es la base de las
gráficas temporales en PPL.

```
source = logs
| where level = "ERROR"
| stats count() as errores by span(@timestamp, 1h) as hora
| sort - hora
| head 4
```

**Resultado real:**

| errores | hora |
|---|---|
| 54 | 2026-06-30 09:00:00 |
| 515 | 2026-06-30 08:00:00 |
| 290 | 2026-06-30 07:00:00 |

> Intervalos: `1h`, `30m`, `1d`, `1w`... Pon un **alias** (`as hora`) si luego quieres `sort` por él.
> Combínalo con `by`: `... by span(@timestamp,1d) as dia, service`.

## 10. `eval` con condiciones y funciones

### Condicional con `if`

```
source = streaming-events-ivan
| eval sev = if(latency_ms > 2000, "alto", "normal")
| stats count() by sev
```

| count() | sev |
|---|---|
| 13762 | alto |
| 86238 | normal |

### Funciones matemáticas y de texto

```
source = streaming-events-ivan
| eval seg = round(latency_ms / 1000.0, 2)
| fields latency_ms, seg
```
`round`, `abs`, `ceil`, `floor`, `sqrt`, `pow`... para números.

```
source = usuarios-ivan
| eval etiqueta = concat(nombre, " (", ciudad, ")")
| fields etiqueta
```
→ `"Juan Martínez Ruiz (Barcelona)"`. Texto: `concat`, `upper`, `lower`, `substring`, `length`, `trim`.

## 11. Filtros más expresivos en `where`

```
source = usuarios-ivan | where ciudad in ("Madrid", "Barcelona")
```
`in (...)` → varios valores de golpe (como un OR).

```
source = logs | where message like "%timeout%" | stats count() by service
```
`like` con comodín `%` → buscar un fragmento de texto. También: `and`, `or`, `not`, `>=`, `!=`.

## 12. Contar valores distintos con `dc()`

`dc()` (distinct count) = cuántos valores únicos hay. Útil para "usuarios únicos", "IPs distintas"...

```
source = streaming-events-ivan
| stats dc(user_id) as usuarios, count() as eventos by service
| sort - usuarios
```

| usuarios | eventos | service |
|---|---|---|
| 4904 | 20163 | cdn-edge |
| 4867 | 17620 | player-api |

## 13. `rare` y excluir columnas

```
source = streaming-events-ivan | rare 3 error_code
```
Los valores **menos** frecuentes (lo contrario de `top`). Útil para anomalías raras.

```
source = usuarios-ivan | fields - bio, intereses, email
```
`fields - a, b` → muestra todo **menos** esos campos (en vez de listar los que quieres).

## 14. Ejemplo avanzado completo (investigación)

"Por hora, errores 5xx de cada servicio, con la latencia media, ordenado por errores":

```
source = streaming-events-ivan
| where status_code >= "500"
| eval grave = if(status_code = "503" or status_code = "504", "sí", "no")
| stats count() as errores, avg(latency_ms) as lat_media by service, grave
| sort - errores
| head 10
```

## 15. Chuleta avanzada

```text
span(@timestamp, 1h) as t        agrupar por ventanas de tiempo
eval x = if(cond, a, b)          columna condicional
eval x = round(n,2) / concat(..) funciones num / texto
where campo in (v1, v2)          varios valores
where texto like "%algo%"        fragmento de texto
stats dc(campo)                  nº de valores distintos
rare N campo                     los menos frecuentes
fields - a, b                    excluir columnas
```

> Nota: existe `parse` (extraer campos de texto con regex) y `grok`/`patterns`, pero su
> comportamiento depende de la versión; pruébalos en tu Query Workbench antes de usarlos en serio.
