# Lab — Logs de Kubernetes con Fluentd (ingesta y flujo de logs)

Simulador de logs de aplicaciones corriendo en **Kubernetes** y recogidos por **Fluentd**,
cargados en OpenSearch. Cubre los contenidos **13 (ingesta y flujo de logs)** y sirve de base para
el **14 (análisis de logs e investigación de incidencias)**.

**Programa:** [`generate_k8s_logs.py`](generate_k8s_logs.py) (Python 3, solo librería estándar).

---

## 1. Qué simula

Tres servicios típicos corriendo en un clúster de Kubernetes, cada uno escribiendo a stdout/stderr,
con sus logs recogidos por un agente **Fluentd** (DaemonSet) y enviados a OpenSearch:

```text
Pods (stdout/stderr)        Agente            OpenSearch
┌──────────────┐
│ postgresql-0 │ ─┐
│ postgresql-1 │  │
├──────────────┤  │      ┌─────────┐      ┌───────────────┐
│ tomcat-xxx   │ ─┼────► │ Fluentd │ ───► │ logs-postgres │ ┐
│ tomcat-yyy   │  │      │ (enrich)│      │ logs-tomcat   │ ├─ alias "logs"
│ tomcat-zzz   │  │      └─────────┘      │ logs-keycloak │ ┘   (y patrón logs-*)
├──────────────┤  │
│ keycloak-0   │ ─┘
│ keycloak-1   │
└──────────────┘
```

| Servicio | Namespace | Índice | Tipo de logs |
|---|---|---|---|
| PostgreSQL | `databases` | `logs-postgres` | LOG/duration/checkpoint, deadlocks, auth fallida (FATAL) |
| Tomcat | `apps` | `logs-tomcat` | catalina/Spring: peticiones HTTP, excepciones Java |
| Keycloak | `iam` | `logs-keycloak` | eventos: LOGIN, LOGOUT, LOGIN_ERROR, CODE_TO_TOKEN |

---

## 2. El enriquecimiento de Fluentd (la clave del contenido 13)

Un log en bruto es solo una línea de texto:

```
2026-06-30 07:34:40.075 UTC [8696] ERROR:  deadlock detected
```

Cuando Fluentd lo recoge en Kubernetes (filtro `kubernetes_metadata`), **añade contexto** para
saber de qué pod/contenedor/namespace viene. El documento que llega a OpenSearch es así:

```json
{
  "@timestamp": "2026-06-30T07:34:40.075Z",
  "service": "postgres",
  "level": "ERROR",
  "message": "deadlock detected",
  "log": "2026-06-30 07:34:40.075 UTC [8696] ERROR:  deadlock detected",
  "stream": "stderr",
  "tag": "kube.var.log.containers.postgresql-0_databases_postgres-9d17b05....log",
  "kubernetes": {
    "namespace_name": "databases",
    "pod_name": "postgresql-0",
    "pod_id": "9e1011c3-f5cd-6fae-a568-c30e99ac5e9a",
    "container_name": "postgres",
    "container_image": "postgres:16.2",
    "container_image_id": "docker-pullable://postgres@sha256:253e84...",
    "host": "ip-10-0-1-23.eu-west-1.compute.internal",
    "labels": { "app": "postgresql", "app_kubernetes_io_name": "postgresql", "tier": "db" },
    "master_url": "https://10.96.0.1:443/api",
    "namespace_id": "756117cf-2d28-f5db-b885-d06d492da8ad"
  },
  "docker": { "container_id": "9d17b05..." },
  "host": "ip-10-0-1-23.eu-west-1.compute.internal",
  "pg_pid": 8696, "pg_level": "ERROR", "db_name": "facturacion", "db_user": "app_rw"
}
```

Ideas para contar en clase:

- **`stream`**: `stdout` / `stderr`. Los errores suelen ir por `stderr`.
- **`tag`**: la ruta del fichero de log dentro del nodo. Fluentd la parsea para sacar pod/ns/container.
- **`kubernetes.*`**: el "quién soy" del log. Permite filtrar *todos los logs de un pod*, *de un
  namespace* o *de un nodo* aunque vengan mezclados de cientos de contenedores.
- **`labels` de-dotted**: las labels de K8s llevan puntos (`app.kubernetes.io/name`). Si se indexan
  tal cual, **chocan** con el mapping (la label `app` no puede ser a la vez texto y objeto). Fluentd
  tiene la opción **`de_dot`** (sustituye `.`→`_`) justo para esto. El simulador hace lo mismo.
- **`message` vs `log`**: `log` es la línea cruda; `message` y los campos `pg_*`/`kc_*`/etc. son el
  resultado de **parsear** esa línea (lo que haría un parser de Fluentd). Esto es lo que permite
  filtrar por `level`, `status_code`, `kc_event_type`... en vez de hacer `grep` sobre texto.

---

## 3. Plantilla de índice + alias (cómo se unifican)

El programa crea una **plantilla de índice** `logs-template` para el patrón `logs-*`. Así:

- Cualquier índice que se llame `logs-*` hereda automáticamente el **mapping** común.
- La plantilla incluye `"aliases": { "logs": {} }`, así que cada `logs-*` se une **solo** al alias `logs`.

```
GET _index_template/logs-template
```

Resultado: puedes consultar los 3 servicios juntos por el **alias `logs`** o por el **patrón `logs-*`**,
sin saber cuántos índices hay detrás. Es el patrón real de un stack de logs (un índice por
servicio/día, todos bajo un alias).

> Esto enlaza con **índices temporales y retención (ISM)**: en producción serían `logs-postgres-2026.06.30`
> y una política ISM los rota/borra a los N días. Aquí lo simplificamos a un índice por servicio.

---

## 4. Cómo ejecutarlo

**Todo de una vez** (borra, crea, carga 10.000 por índice y se queda goteando ~5/min):
```bash
python3 generate_k8s_logs.py --reset --initial 10000 --rate 5
```

**Solo el goteo en vivo** (si los iniciales ya están cargados):
```bash
python3 generate_k8s_logs.py --no-initial --rate 5
```

Salida del bucle (una línea por minuto, para verlo en directo):
```
▶ goteo en vivo: ~5/min por índice. Ctrl+C para parar.
[min 1] 12:03:11  +  postgres:6  tomcat:4  keycloak:5
[min 2] 12:04:11  +  postgres:5  tomcat:7  keycloak:3
```
Se para con **Ctrl+C**.

### Parámetros

| Flag | Por defecto | Qué hace |
|---|---|---|
| `--initial` | 10000 | docs iniciales por índice |
| `--rate` | 5 | docs/min por índice en el bucle (aleatorio alrededor de ese número) |
| `--spread-hours` | 6 | en qué ventana hacia atrás reparte los docs iniciales |
| `--reset` | — | borra los índices antes de crear |
| `--no-initial` | — | salta la carga inicial (solo bucle) |
| `--no-loop` | — | solo setup + carga inicial (no se queda corriendo) |
| `--host` / `--user` / `--password` | clúster del curso / admin | conexión |

---

## 5. En OpenSearch Dashboards

Crear el **data view**: ☰ → Dashboards Management → Data Views → `logs-*`, time field `@timestamp`.

Comprobaciones (Dev Tools):
```
GET logs/_count
GET _cat/indices/logs-*?v
GET logs/_search
{ "size": 0, "aggs": { "por_servicio": { "terms": { "field": "service" } } } }
```

---

## 6. Consultas e investigación de incidencias (puente al contenido 14)

```
# Todos los errores de los últimos 30 min, de cualquier servicio (vía alias)
GET logs/_search
{ "size": 20, "sort": [{ "@timestamp": "desc" }],
  "query": { "bool": { "filter": [
    { "terms": { "level": ["ERROR","FATAL"] } },
    { "range": { "@timestamp": { "gte": "now-30m" } } } ] } } }
```

```
# Logs de un pod concreto (lo que harías al investigar una caída)
GET logs/_search
{ "query": { "term": { "kubernetes.pod_name": "postgresql-0" } } }
```

```
# Errores de login de Keycloak por IP (¿ataque de fuerza bruta?)
GET logs-keycloak/_search
{ "size": 0, "query": { "term": { "kc_event_type": "LOGIN_ERROR" } },
  "aggs": { "por_ip": { "terms": { "field": "ip_address", "size": 10 } } } }
```

```
# Tasa de errores por servicio en el tiempo (correlación de incidencias)
GET logs/_search
{ "size": 0,
  "query": { "term": { "level": "ERROR" } },
  "aggs": { "t": { "date_histogram": { "field": "@timestamp", "fixed_interval": "5m" },
    "aggs": { "svc": { "terms": { "field": "service" } } } } } }
```

Ideas de dashboard de logs: KPI de errores/min, serie temporal de `level` por servicio, top
`kubernetes.pod_name` con más errores, top `exception` (tomcat), `kc_event_type` (keycloak),
tabla de últimos errores con `kubernetes.pod_name` + `message`.

---

## 7. Notas (clúster compartido)

- El alias `logs` y los índices `logs-*` son **globales** en el clúster. Si varios alumnos cargan
  `logs-*`, se mezclan bajo el mismo alias.
- Para aislarlo por persona: añadir un sufijo (`logs-postgres-ivan`…) y un alias propio (`logs-ivan`).
  El programa se puede parametrizar para ello.
- Limpieza al terminar:
  ```
  DELETE logs-postgres
  DELETE logs-tomcat
  DELETE logs-keycloak
  DELETE _index_template/logs-template
  ```

---

## Resumen

```text
Caso        → 3 servicios en K8s (postgres/tomcat/keycloak), logs vía Fluentd
Enriquecido → kubernetes.{pod,ns,container,node,labels}, tag, stream, docker.container_id
Unificado   → plantilla logs-* + alias "logs"  (1 mapping, N índices)
Programa    → carga 10.000/índice y luego ~5/min en vivo (Ctrl+C para parar)
Enlaza con  → contenido 13 (ingesta/pipeline/templates) y 14 (investigación de incidencias)
```
