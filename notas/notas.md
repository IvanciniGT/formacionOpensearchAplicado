# Día 3 — Explotación de datos

> "Ya sabemos crear e indexar datos. Hoy vamos a aprender a hacer preguntas útiles sobre esos datos."

Venimos de dos días:
- **Día 1**: teoría. Qué es OpenSearch, Lucene, índices, shards, índice invertido, logs vs contenidos, almacenamiento.
- **Día 2**: lab. Índice `usuarios-ivan`, mappings, analizadores, `_analyze`, `_bulk`, queries básicas, shards y stats.

Hoy toca cubrir principalmente:

```text
4. Query DSL
5. Agregaciones y análisis de datos
6. Discover
```

---

# 1. Recap muy corto (10 min máximo)

> "El primer día vimos POR QUÉ existe OpenSearch. Ayer creamos un índice real, definimos mappings, probamos analizadores, cargamos documentos y lanzamos consultas básicas. Hoy vamos a EXPLOTAR esos datos: búsquedas más finas, filtros, combinaciones, agregaciones y exploración visual desde Discover."

Comandos para calentar (Dev Tools):

```http
GET usuarios-ivan/_count

GET usuarios-ivan/_mapping

GET usuarios-ivan/_search
{
  "query": { "match_all": {} }
}
```

Ojo: ayer terminamos **borrando** el índice, así que hoy empezamos recreándolo. El apartado 0 del lab de hoy trae el `PUT` + `_bulk` condensados (es lo mismo del día 2) para volver a tener los 6 documentos en dos comandos. Y recordad: clúster compartido → cada uno usa **su** índice `usuarios-<nombre>`.

---

# 2. Query DSL con criterio

El mensaje principal:

> "Query DSL no es escribir JSON porque sí. Es la forma de decirle a OpenSearch QUÉ quiero encontrar y CÓMO quiero combinar condiciones."

## 2.1 `match` vs `term`

La distinción más importante del día. Si esto se entiende, lo demás va rodado.

```text
match → búsqueda TEXTUAL, pasa por el analyzer (tokeniza, minúsculas, acentos...)
term  → búsqueda EXACTA, NO analiza el texto
```

Recordad el día 1: los campos `text` se guardan en un índice invertido (tokenizados, normalizados...). Los campos `keyword` se guardan tal cual.

- Un `match` aplica al término de búsqueda **el mismo proceso** que se aplicó al indexar → por eso "encuentra parecidos".
- Un `term` busca el byte exacto → por eso solo sirve bien en `keyword`, números, fechas, booleanos.

Ejemplo textual (sobre `bio`, que es `text`):

```http
GET usuarios-ivan/_search
{
  "query": { "match": { "bio": "datos" } }
}
```

> "Esto busca documentos cuya bio tenga relación textual con 'datos'. Como `bio` es `text`, se analiza."

Ejemplo exacto (sobre `ciudad`, que es `keyword`):

```http
GET usuarios-ivan/_search
{
  "query": { "term": { "ciudad": "Madrid" } }
}
```

> "Esto NO busca parecido. Busca EXACTAMENTE Madrid. Por eso `ciudad` está como `keyword`."

**El error típico:** hacer `term` sobre un campo `text`. Como el campo se guardó tokenizado y en minúsculas, `term: { bio: "Datos" }` con mayúscula no encuentra nada. El término de búsqueda no pasa por el analyzer, pero lo guardado sí pasó. → No casan.

## 2.2 Rango

```http
GET usuarios-ivan/_search
{
  "query": {
    "range": {
      "edad": { "gte": 30, "lte": 40 }
    }
  }
}
```

> "Los rangos tienen sentido en campos NUMÉRICOS y FECHAS. Aquí ya no hablamos de texto, sino de comparación."

Operadores: `gte` (≥), `gt` (>), `lte` (≤), `lt` (<).

## 2.3 `bool`: la pieza clave

Aquí hay que detenerse. Es lo más importante del bloque de Query DSL.

```text
must     → TIENE que cumplirse y SÍ puntúa (afecta al score / relevancia)
filter   → TIENE que cumplirse, pero NO puntúa (y se cachea → más rápido)
must_not → EXCLUYE
should   → DEBERÍA cumplirse (preferencia / opcional según el caso)
```

La diferencia entre `must` y `filter` es sutil pero importante:
- `must` participa en el cálculo de relevancia (score). Útil en búsquedas de texto donde quiero ordenar por "lo más relevante".
- `filter` es un sí/no binario: cumple o no cumple. No calcula score → es **más eficiente y se cachea**. Para filtros exactos (activo, ciudad, rango de fechas) usa SIEMPRE `filter`.

Ejemplo completo:

```http
GET usuarios-ivan/_search
{
  "query": {
    "bool": {
      "must":     [ { "match": { "bio": "datos" } } ],
      "filter":   [ { "term":  { "activo": true } } ],
      "must_not": [ { "term":  { "ciudad": "Madrid" } } ]
    }
  }
}
```

> "Quiero usuarios cuya bio hable de datos, que estén activos, pero que NO sean de Madrid."

## 2.4 `should` bien explicado

Esto suele liar. La clave: **`should` cambia de comportamiento según si hay o no `must`/`filter`**.

**Caso 1: hay un `must` → `should` es solo preferencia (sube relevancia, no obliga).**

```http
GET usuarios-ivan/_search
{
  "query": {
    "bool": {
      "must":   [ { "match": { "bio": "datos" } } ],
      "should": [ { "term":  { "ciudad": "Madrid" } } ]
    }
  }
}
```

> "Aquí Madrid NO es obligatorio. Si además es de Madrid, sube relevancia y aparece más arriba. Pero no excluye a los demás."

**Caso 2: `should` a secas (sin `must`/`filter`) → al menos uno DEBE cumplirse.**

```http
GET usuarios-ivan/_search
{
  "query": {
    "bool": {
      "should": [
        { "term": { "ciudad": "Madrid" } },
        { "term": { "ciudad": "Barcelona" } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

> "Esto es un OR: dame los de Madrid O los de Barcelona."

`minimum_should_match` hace explícito cuántas de las cláusulas `should` deben cumplirse. Sin `must`/`filter`, por defecto ya es 1; con `must`/`filter` presente, por defecto es 0 (solo preferencia). Ponerlo explícito evita sorpresas.

## 2.5 `_source`, orden y paginación

```http
GET usuarios-ivan/_search
{
  "_source": ["nombre", "edad", "ciudad"],
  "from": 0,
  "size": 3,
  "sort": [ { "edad": "desc" } ],
  "query": { "match_all": {} }
}
```

> "No siempre quiero todo el documento. Puedo elegir CAMPOS (`_source`), PAGINAR (`from`/`size`) y ORDENAR (`sort`)."

Ojo con el orden sobre `text`: no se puede ordenar bien por un campo `text` (está tokenizado). Por eso en el día 2 creamos `nombre.raw` (`keyword`): para ordenar/agregar usamos el sub-campo `keyword`, no el `text`.

---

# 3. Agregaciones

Mensaje principal:

> "Una BÚSQUEDA devuelve documentos. Una AGREGACIÓN devuelve información resumida."

```text
_search normal → dame DOCUMENTOS
aggs           → dame MÉTRICAS, conteos, agrupaciones, tendencias
```

Truco clave: `"size": 0`. Le dice a OpenSearch "no me devuelvas documentos, solo el resultado de la agregación". Si no lo pones, te trae los documentos Y la agregación (más lento y más ruido).

## 3.1 Agrupar por ciudad (`terms`)

```http
GET usuarios-ivan/_search
{
  "size": 0,
  "aggs": {
    "usuarios_por_ciudad": {
      "terms": { "field": "ciudad" }
    }
  }
}
```

> "Esto ya no me interesa por los documentos individuales. Me interesa CUÁNTOS usuarios tengo por ciudad."

Devuelve "buckets" (cubos): un grupo por cada valor distinto de `ciudad`, con su `doc_count`. Es el equivalente al `GROUP BY` de SQL. Funciona sobre `keyword`, no sobre `text`.

## 3.2 Media de edad (`avg`)

```http
GET usuarios-ivan/_search
{
  "size": 0,
  "aggs": {
    "edad_media": {
      "avg": { "field": "edad" }
    }
  }
}
```

`terms` es una agregación de **bucket** (agrupa). `avg`/`min`/`max`/`sum` son agregaciones de **métrica** (calculan un número). La gracia viene al combinarlas.

## 3.3 Agrupación + métrica dentro (anidadas)

```http
GET usuarios-ivan/_search
{
  "size": 0,
  "aggs": {
    "por_ciudad": {
      "terms": { "field": "ciudad" },
      "aggs": {
        "edad_media": {
          "avg": { "field": "edad" }
        }
      }
    }
  }
}
```

> "Agrupo por ciudad y DENTRO de cada ciudad calculo la edad media."

Esto es el corazón del análisis de datos: bucket → métrica dentro. Equivale a `SELECT ciudad, AVG(edad) FROM usuarios GROUP BY ciudad`.

## 3.4 Estadísticas generales (`stats`)

```http
GET usuarios-ivan/_search
{
  "size": 0,
  "aggs": {
    "estadisticas_edad": {
      "stats": { "field": "edad" }
    }
  }
}
```

Devuelve de un golpe:

```text
count
min
max
avg
sum
```

## 3.5 Relación con dashboards (el puente a mañana)

```text
terms             → tablas, rankings, tartas (pie)
avg / max / min   → KPIs (un numerito grande)
stats             → resumen numérico
date_histogram    → gráficas temporales (evolución en el tiempo)
percentiles       → latencias (p50, p95, p99)
```

> "Lo que mañana veremos como una gráfica en Dashboards muchas veces NO es magia: por debajo hay una agregación. La gráfica solo es la cara bonita del `aggs`."

---

# 4. Discover

Aquí cambiamos de API a interfaz.

> "Discover es la forma VISUAL de explorar documentos sin escribir Query DSL todo el rato."

Pasos:

```text
1. Entrar en OpenSearch Dashboards
2. Ir a Discover (menú ☰)
3. Seleccionar o crear el data view (index pattern) usuarios-ivan*
4. Elegir campo temporal si aplica: fecha_registro
5. Ver documentos
6. Añadir columnas: nombre, ciudad, edad, activo
7. Filtrar ciudad = Madrid
8. Filtrar activo = true
9. Buscar texto en bio
10. Guardar la búsqueda
```

> "Discover NO es un dashboard. Es una herramienta de EXPLORACIÓN. Sirve para investigar datos, comprobar si llegan bien, filtrar, buscar y guardar vistas útiles."

Las tres herramientas y cuándo usar cada una:

```text
Dev Tools  → control técnico mediante API (lo que llevamos haciendo)
Discover   → exploración visual de documentos
Dashboard  → panel de seguimiento ya diseñado (mañana)
```

Nota práctica: el **data view** (antes "index pattern") es lo que conecta Dashboards con el índice. `usuarios-ivan*` con `*` para que cubra también `usuarios-ivan_v2` o futuros índices con ese prefijo. El campo temporal (`fecha_registro`) es lo que activa la línea de tiempo y los filtros por rango de fechas.

---

# 5. Cierre del día

> "Hoy hemos pasado de TENER datos indexados a HACER PREGUNTAS útiles sobre ellos. Hemos visto cómo combinar condiciones con Query DSL, cómo resumir datos con agregaciones y cómo explorarlos visualmente con Discover. Mañana construiremos visualizaciones y dashboards a partir de estas mismas ideas."

## Resumen de hoy (para ellos)

```text
Hoy hemos visto:
- match vs term  (texto analizado vs exacto)
- range          (numéricos y fechas)
- bool: must, filter, must_not, should
- minimum_should_match
- _source, orden y paginación
- agregaciones: terms, avg, stats
- agregaciones anidadas (bucket + métrica)
- relación entre agregaciones y visualizaciones
- Discover como herramienta de exploración
```
