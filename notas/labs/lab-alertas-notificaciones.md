# Lab — Alertas y Notificaciones (contenidos 11 y 12)

Plugins: **opensearch-alerting** + **opensearch-notifications** (ambos instalados en el clúster).
Caso: alertar sobre los incidentes del índice `streaming-events-ivan`.

> Comandos `POST/GET` = Dev Tools. Pasos `☰ →` = interfaz de Dashboards.

---

## 0. Las 3 piezas del modelo de alertas

```text
MONITOR    → CADA cuánto y QUÉ consulto (una búsqueda programada)
TRIGGER    → CONDICIÓN que evalúo sobre el resultado (ej. count > 100)
ACTION     → QUÉ hago si se cumple (notificar a un CANAL)
CANAL      → A DÓNDE va la notificación (email, Slack, Teams, webhook)
```

Flujo: el **monitor** lanza su búsqueda cada X minutos → el **trigger** evalúa el resultado →
si se cumple, la **action** manda un mensaje al **canal** de notificaciones.

Tipos de monitor:
- **Per query (query_level)**: una condición sobre el total de la búsqueda. El más común.
- **Per bucket (bucket_level)**: condición por cada grupo de una agregación (ej. "alerta por cada
  servicio que supere X errores"). Ideal para no crear 9 monitores, uno por servicio.
- **Per document (document_level)**: dispara por documentos concretos que cumplen una query.
- **Per cluster metrics**: sobre la salud/estado del clúster.

---

## 1. Crear un canal de notificaciones

Antes de la alerta necesitas a dónde mandarla. **☰ → Notifications → Channels → Create channel.**

### 1.1 Slack / Teams / webhook (lo más fácil para demo)

```text
Name:        slack-ops
Channel type: Slack            (Teams y "Custom webhook" son análogos)
Webhook URL:  https://hooks.slack.com/services/XXX/YYY/ZZZ
→ Create
```

> Slack y Teams son, por debajo, **webhooks**. "Custom webhook" sirve para cualquier sistema
> (PagerDuty, un bot propio, etc.).

### 1.2 Email

Email necesita además un **sender** (servidor SMTP) y una **lista de destinatarios**:

```text
☰ → Notifications → Email senders → Create  (host, puerto, from, TLS)
☰ → Notifications → Email recipient groups → Create
☰ → Notifications → Channels → Create → type Email → elige sender + grupo
```

### 1.3 Por API (Dev Tools)

```
POST _plugins/_notifications/configs
{
  "config_id": "slack-ops",
  "name": "slack-ops",
  "config": {
    "name": "slack-ops",
    "description": "Canal Slack del equipo de operaciones",
    "config_type": "slack",
    "is_enabled": true,
    "slack": { "url": "https://hooks.slack.com/services/XXX/YYY/ZZZ" }
  }
}
```

Probar que el canal funciona:

```
GET _plugins/_notifications/feature/test/slack-ops
```

---

## 2. Alerta 1 — Pico de errores CDN (incidente 1)

Monitor *per query*: cuenta `CDN_TIMEOUT` en la última hora; si supera un umbral, avisa.
Se modela igual el resto: cambia la query y la condición.

> En clase, usa `now-14d` para que dispare con los datos históricos. En real sería `now-1h`.

```
POST _plugins/_alerting/monitors
{
  "type": "monitor",
  "name": "streaming - pico CDN_TIMEOUT",
  "monitor_type": "query_level_monitor",
  "enabled": true,
  "schedule": { "period": { "interval": 5, "unit": "MINUTES" } },
  "inputs": [{
    "search": {
      "indices": ["streaming-events-ivan"],
      "query": {
        "size": 0,
        "query": { "bool": { "filter": [
          { "term":  { "error_code": "CDN_TIMEOUT" } },
          { "range": { "@timestamp": { "gte": "now-1h" } } }
        ]}}
      }
    }
  }],
  "triggers": [{
    "name": "demasiados timeouts",
    "severity": "1",
    "condition": { "script": {
      "source": "ctx.results[0].hits.total.value > 100",
      "lang": "painless"
    }},
    "actions": [{
      "name": "avisar-slack",
      "destination_id": "slack-ops",
      "message_template": {
        "source": "🚨 CDN_TIMEOUT: {{ctx.results.0.hits.total.value}} errores en la última hora. Monitor: {{ctx.monitor.name}}",
        "lang": "mustache"
      },
      "subject_template": { "source": "Alerta CDN", "lang": "mustache" }
    }]
  }]
}
```

> `ctx.results[0].hits.total.value` = el total de la búsqueda. `ctx` lleva todo el contexto
> (monitor, trigger, resultados) y se interpola en el mensaje con plantillas **mustache**.

**Probar el monitor sin esperar al schedule** (`dryrun` no persiste ni notifica):

```
POST _plugins/_alerting/monitors/_execute?dryrun=true
{ ... el mismo cuerpo del monitor ... }
```
→ Verificado contra el clúster: con `now-14d` devuelve `hits.total ≈ 3858` y `triggered: true`.

---

## 3. Alerta 2 — Latencia alta (incidente 2)

Igual, pero la métrica es la **media de latencia** (o un percentil) en vez de un conteo.
Usamos una agregación y la condición la lee de `ctx.results[0].aggregations`:

```
POST _plugins/_alerting/monitors
{
  "type": "monitor",
  "name": "streaming - latencia alta",
  "monitor_type": "query_level_monitor",
  "enabled": true,
  "schedule": { "period": { "interval": 5, "unit": "MINUTES" } },
  "inputs": [{
    "search": {
      "indices": ["streaming-events-ivan"],
      "query": {
        "size": 0,
        "query": { "range": { "@timestamp": { "gte": "now-1h" } } },
        "aggs": { "lat_media": { "avg": { "field": "latency_ms" } } }
      }
    }
  }],
  "triggers": [{
    "name": "latencia media > 800ms",
    "severity": "2",
    "condition": { "script": {
      "source": "ctx.results[0].aggregations.lat_media.value > 800",
      "lang": "painless"
    }},
    "actions": []
  }]
}
```

---

## 4. Alerta 3 — Errores por servicio (per bucket)

Un monitor *per bucket* alerta **por cada grupo** que cumpla la condición: aquí, cada servicio con
más de 200 errores. Evita tener 9 monitores (uno por servicio).

```
POST _plugins/_alerting/monitors
{
  "type": "monitor",
  "name": "streaming - errores por servicio",
  "monitor_type": "bucket_level_monitor",
  "enabled": true,
  "schedule": { "period": { "interval": 10, "unit": "MINUTES" } },
  "inputs": [{
    "search": {
      "indices": ["streaming-events-ivan"],
      "query": {
        "size": 0,
        "query": { "bool": { "filter": [
          { "term": { "is_error": true } },
          { "range": { "@timestamp": { "gte": "now-1h" } } }
        ]}},
        "aggregations": {
          "por_servicio": {
            "terms": { "field": "service", "size": 20 }
          }
        }
      }
    }
  }],
  "triggers": [{
    "bucket_level_trigger": {
      "name": "servicio con muchos errores",
      "severity": "1",
      "condition": {
        "buckets_path": { "count": "_count" },
        "parent_bucket_path": "por_servicio",
        "script": { "source": "params.count > 200", "lang": "painless" }
      },
      "actions": []
    }
  }]
}
```

> El resultado del trigger incluye **qué buckets** (servicios) dispararon; en la action puedes
> listarlos con `{{ctx.newAlerts}}`.

---

## 5. Alerta 4 — Ausencia de logs ("dead man's switch")

Caso clave en observabilidad: que un servicio **deje de mandar datos** (cayó el agente, cayó el
servicio). Se alerta cuando el conteo es **0** (o muy bajo) en la ventana reciente:

```
POST _plugins/_alerting/monitors
{
  "type": "monitor",
  "name": "streaming - ausencia de eventos analytics-ingest",
  "monitor_type": "query_level_monitor",
  "enabled": true,
  "schedule": { "period": { "interval": 5, "unit": "MINUTES" } },
  "inputs": [{
    "search": {
      "indices": ["streaming-events-ivan"],
      "query": {
        "size": 0,
        "query": { "bool": { "filter": [
          { "term":  { "service": "analytics-ingest" } },
          { "range": { "@timestamp": { "gte": "now-15m" } } }
        ]}}
      }
    }
  }],
  "triggers": [{
    "name": "sin datos en 15 min",
    "severity": "1",
    "condition": { "script": {
      "source": "ctx.results[0].hits.total.value == 0",
      "lang": "painless"
    }},
    "actions": []
  }]
}
```

> Con datos históricos esta no disparará (sí hay eventos). Es la que enseña el concepto:
> **alertar por lo que NO llega**, no solo por lo que falla.

---

## 6. Gestionar monitores y alertas

```
GET  _plugins/_alerting/monitors/_search        # listar monitores (query match_all)
GET  _plugins/_alerting/monitors/<monitor_id>   # ver uno
POST _plugins/_alerting/monitors/<id>/_execute  # ejecutar ahora
DELETE _plugins/_alerting/monitors/<id>         # borrar
```

En interfaz: **☰ → Alerting** → pestañas **Monitors**, **Alerts** (historial de disparos),
**Destinations/Channels**.

Estados de una alerta: `ACTIVE` (condición cumplida, sigue), `ACKNOWLEDGED` (alguien la reconoció),
`COMPLETED` (la condición dejó de cumplirse), `ERROR`.

---

## 7. Buenas prácticas (reducir ruido y falsas alarmas)

```text
- Umbral con margen: no alertes a la primera. Usa números que indiquen problema REAL.
- Ventana adecuada: now-5m/now-15m según la frecuencia del dato.
- Severidades: 1 (crítico) ... 5 (info). No todo es crítico.
- "throttle" en la action: no repetir el aviso cada 5 min mientras dure el incidente.
- Per-bucket en vez de N monitores: un monitor por dimensión, no uno por valor.
- Dead-man's switch: alerta también por AUSENCIA de datos.
- Prueba con dryrun antes de habilitar.
- Cada alerta debe ser ACCIONABLE: si nadie hace nada al recibirla, sobra.
```

`throttle` en una action (no repetir antes de 30 min):

```
"throttle_enabled": true,
"throttle": { "value": 30, "unit": "MINUTES" }
```

---

## Resumen

```text
Notifications → crear CANAL (slack/email/webhook) y probarlo
Alerting      → MONITOR (qué+cuándo) + TRIGGER (condición) + ACTION (canal+mensaje)
Tipos        → per query / per bucket / per document / cluster metrics
Casos clave  → pico de errores, latencia, errores por servicio, AUSENCIA de logs
Ruido        → umbrales, throttle, severidades, alertas accionables
```
