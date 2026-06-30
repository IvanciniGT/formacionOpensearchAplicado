#!/usr/bin/env python3
"""
Simulador de logs de Kubernetes recogidos por Fluentd, para OpenSearch.

Crea 3 índices (logs-postgres, logs-tomcat, logs-keycloak) con documentos de log
ENRIQUECIDOS como lo hace el filtro kubernetes_metadata de Fluentd:
objeto `kubernetes` (namespace, pod, container, node, labels...), `docker.container_id`,
`stream` (stdout/stderr) y `tag`. Todos quedan bajo el alias `logs` y el patrón `logs-*`.

Flujo:
  1) crea una plantilla de índice `logs-*` (mapping + alias `logs`),
  2) crea los 3 índices,
  3) carga N documentos iniciales en cada uno (por defecto 10.000),
  4) se queda en bucle metiendo ~5/min nuevos en cada índice (aleatorio) hasta Ctrl+C.

Solo librería estándar. Uso típico:
  python3 generate_k8s_logs.py --initial 10000 --rate 5
  python3 generate_k8s_logs.py --reset --initial 10000 --rate 5      # borra y recrea
  python3 generate_k8s_logs.py --no-initial --rate 5                 # solo el goteo en vivo
"""

import argparse
import base64
import json
import random
import ssl
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------------- #
# Cliente HTTP mínimo (HTTPS con cert autofirmado + basic auth)
# --------------------------------------------------------------------------- #

class OS:
    def __init__(self, host, user, password):
        self.host = host.rstrip("/")
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    def req(self, method, path, body=None, ndjson=False):
        data = None
        if body is not None:
            data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
        r = urllib.request.Request(self.host + path, data=data, method=method)
        r.add_header("Authorization", self.auth)
        r.add_header("Content-Type", "application/x-ndjson" if ndjson else "application/json")
        try:
            with urllib.request.urlopen(r, context=self.ctx, timeout=120) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))


# --------------------------------------------------------------------------- #
# Catálogos de Kubernetes (topología simulada del clúster)
# --------------------------------------------------------------------------- #

NODES = [
    "ip-10-0-1-23.eu-west-1.compute.internal",
    "ip-10-0-2-47.eu-west-1.compute.internal",
    "ip-10-0-3-88.eu-west-1.compute.internal",
]

def _id(n):  # id hex estable tipo k8s/docker
    return "".join(random.choice("0123456789abcdef") for _ in range(n))

def make_pods(service, namespace, container, image, labels, names):
    # de_dot: Fluentd sustituye '.'/'/' en las claves de labels para no romper el mapping
    labels = {k.replace(".", "_").replace("/", "_"): v for k, v in labels.items()}
    pods = []
    for name in names:
        pods.append({
            "namespace_name": namespace,
            "pod_name": name,
            "pod_id": f"{_id(8)}-{_id(4)}-{_id(4)}-{_id(4)}-{_id(12)}",
            "container_name": container,
            "container_image": image,
            "container_image_id": f"docker-pullable://{image.split(':')[0]}@sha256:{_id(64)}",
            "host": random.choice(NODES),
            "labels": labels,
            "master_url": "https://10.96.0.1:443/api",
            "namespace_id": f"{_id(8)}-{_id(4)}-{_id(4)}-{_id(4)}-{_id(12)}",
            "_docker_id": _id(64),
        })
    return pods

# topología por servicio (réplicas de cada workload)
TOPOLOGY = {
    "postgres": make_pods(
        "postgres", "databases", "postgres", "postgres:16.2",
        {"app": "postgresql", "app.kubernetes.io/name": "postgresql", "tier": "db", "statefulset.kubernetes.io/pod-name": "postgresql"},
        ["postgresql-0", "postgresql-1"]),
    "tomcat": make_pods(
        "tomcat", "apps", "tomcat", "tomcat:9.0-jdk17",
        {"app": "tomcat", "app.kubernetes.io/name": "tomcat", "tier": "backend"},
        [f"tomcat-7d9f8c6b5d-{_id(5)}" for _ in range(3)]),
    "keycloak": make_pods(
        "keycloak", "iam", "keycloak", "quay.io/keycloak/keycloak:24.0",
        {"app": "keycloak", "app.kubernetes.io/name": "keycloak", "tier": "auth"},
        ["keycloak-0", "keycloak-1"]),
}

INDEX = {"postgres": "logs-postgres", "tomcat": "logs-tomcat", "keycloak": "logs-keycloak"}


# --------------------------------------------------------------------------- #
# Generadores de líneas de log por servicio
# --------------------------------------------------------------------------- #

def _ip():
    return f"10.0.{random.randint(0,5)}.{random.randint(2,250)}"

def _cli_ip():
    return f"{random.randint(80,200)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

PG_DBS = ["ventas", "catalogo", "usuarios", "facturacion"]
PG_USERS = ["app_rw", "app_ro", "reporting", "postgres"]
PG_TABLES = ["orders", "customers", "invoices", "products", "sessions"]

def gen_postgres(now):
    roll = random.random()
    duration_ms = None
    db = random.choice(PG_DBS); user = random.choice(PG_USERS); table = random.choice(PG_TABLES)
    if roll < 0.80:      # LOG (INFO)
        pglevel = "LOG"; lvl = "INFO"
        opt = random.random()
        if opt < 0.45:
            duration_ms = round(random.triangular(0.3, 800, 8), 3)
            msg = f"duration: {duration_ms} ms  statement: SELECT * FROM {table} WHERE id = {random.randint(1,99999)}"
        elif opt < 0.6:
            msg = f"connection received: host={_cli_ip()} port={random.randint(30000,60000)}"
        elif opt < 0.75:
            msg = f"connection authorized: user={user} database={db}"
        elif opt < 0.88:
            msg = f"checkpoint complete: wrote {random.randint(50,5000)} buffers ({random.randint(1,30)}.%); {random.randint(0,3)} WAL file(s) added"
        else:
            msg = f"disconnection: session time: 0:{random.randint(0,59):02d}:{random.randint(0,59):02d}.{random.randint(0,999):03d} user={user} database={db}"
    elif roll < 0.93:    # WARNING
        pglevel = "WARNING"; lvl = "WARN"
        msg = random.choice([
            "could not receive data from client: Connection reset by peer",
            f"skipping vacuum of \"{table}\" --- lock not available",
            "there is already a transaction in progress",
            f"autovacuum of table \"{db}.public.{table}\" is taking long",
        ])
    elif roll < 0.99:    # ERROR
        pglevel = "ERROR"; lvl = "ERROR"
        msg = random.choice([
            f"relation \"{table}\" does not exist at character 15",
            f"duplicate key value violates unique constraint \"{table}_pkey\"",
            "deadlock detected",
            f"syntax error at or near \"{random.choice(['FORM','SELCT','WHRE'])}\"",
        ])
    else:                # FATAL
        pglevel = "FATAL"; lvl = "FATAL"
        msg = random.choice([
            f"password authentication failed for user \"{user}\"",
            "remaining connection slots are reserved for non-replication superuser connections",
            "terminating connection due to administrator command",
        ])
    pid = random.randint(100, 9999)
    raw = f"{now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} UTC [{pid}] {pglevel}:  {msg}"
    parsed = {"pg_pid": pid, "pg_level": pglevel, "db_name": db, "db_user": user, "logger": "postgres"}
    if duration_ms is not None:
        parsed["duration_ms"] = duration_ms
    return lvl, msg, raw, parsed

TC_LOGGERS = ["org.apache.catalina.core.StandardService", "org.springframework.web.servlet.DispatcherServlet",
              "com.empresa.api.OrderController", "com.empresa.api.AuthController", "org.hibernate.SQL",
              "org.apache.coyote.http11.Http11Processor", "com.empresa.service.PaymentService"]
TC_PATHS = ["/api/orders", "/api/customers", "/api/products", "/api/login", "/api/cart", "/health"]
TC_EXC = ["java.lang.NullPointerException", "java.net.SocketTimeoutException",
          "org.springframework.dao.DataAccessResourceFailureException",
          "java.sql.SQLException: connection timed out", "java.lang.IllegalStateException"]

def gen_tomcat(now):
    roll = random.random()
    thread = random.choice([f"http-nio-8080-exec-{random.randint(1,20)}", "main", f"Catalina-utility-{random.randint(1,4)}"])
    logger = random.choice(TC_LOGGERS)
    exception = None; status = None; resp_ms = None; path = None
    if roll < 0.80:      # INFO
        lvl = "INFO"
        opt = random.random()
        if opt < 0.5:
            path = random.choice(TC_PATHS); status = random.choice(["200","200","200","201","204","302"])
            resp_ms = random.randint(2, 600)
            msg = f"{random.choice(['GET','POST','PUT'])} {path} {status} in {resp_ms}ms"
        elif opt < 0.7:
            msg = f"Initializing Spring DispatcherServlet 'dispatcherServlet'"
        elif opt < 0.85:
            msg = f"Server startup in [{random.randint(3000,12000)}] milliseconds"
        else:
            msg = f"Completed initialization in {random.randint(1,40)} ms"
    elif roll < 0.93:    # WARN
        lvl = "WARN"
        msg = random.choice([
            f"Slow query detected: {random.randint(800,5000)}ms",
            f"Connection pool stats: active={random.randint(8,20)} idle={random.randint(0,5)} waiting={random.randint(0,8)}",
            "The web application appears to have started a thread but has failed to stop it",
        ])
    elif roll < 0.985:   # ERROR
        lvl = "ERROR"; exception = random.choice(TC_EXC)
        path = random.choice(TC_PATHS); status = "500"
        msg = f"Servlet.service() for servlet [dispatcher] in context threw exception [{exception}]"
    else:                # SEVERE -> ERROR
        lvl = "ERROR"; exception = random.choice(TC_EXC)
        msg = f"Unexpected error processing request: {exception}"
    raw = f"{now.strftime('%d-%b-%Y %H:%M:%S.%f')[:-3]} {lvl} [{thread}] {logger} - {msg}"
    parsed = {"logger": logger, "thread": thread}
    if exception: parsed["exception"] = exception
    if status: parsed["status_code"] = status
    if resp_ms is not None: parsed["response_ms"] = resp_ms
    if path: parsed["request_path"] = path
    return lvl, msg, raw, parsed

KC_REALMS = ["master", "empresa", "partners"]
KC_CLIENTS = ["account", "frontend-web", "mobile-app", "grafana", "admin-cli"]
KC_OK_EVENTS = ["LOGIN", "LOGOUT", "CODE_TO_TOKEN", "REFRESH_TOKEN", "REGISTER", "UPDATE_PROFILE"]

def gen_keycloak(now):
    thread = f"executor-thread-{random.randint(1,30)}"
    realm = random.choice(KC_REALMS); client = random.choice(KC_CLIENTS)
    uid = f"{_id(8)}-{_id(4)}-{_id(4)}-{_id(4)}-{_id(12)}"; ip = _cli_ip()
    error = None
    roll = random.random()
    if roll < 0.85:      # evento OK -> INFO
        lvl = "INFO"; event = random.choice(KC_OK_EVENTS)
        body = f"type={event}, realmId={realm}, clientId={client}, userId={uid}, ipAddress={ip}"
    elif roll < 0.97:    # error de login -> WARN
        lvl = "WARN"; event = "LOGIN_ERROR"
        error = random.choice(["invalid_user_credentials", "user_not_found", "account_disabled", "expired_code"])
        body = f"type={event}, realmId={realm}, clientId={client}, userId={uid}, ipAddress={ip}, error={error}"
    else:                # error de servicio -> ERROR
        lvl = "ERROR"; event = "CODE_TO_TOKEN_ERROR"
        error = random.choice(["invalid_client_credentials", "invalid_redirect_uri"])
        body = f"type={event}, realmId={realm}, clientId={client}, error={error}"
    logger = "org.keycloak.events"
    raw = f"{now.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]} {lvl}  [{logger}] ({thread}) {body}"
    parsed = {"logger": logger, "thread": thread, "kc_event_type": event, "realm": realm,
              "client_id": client, "user_id": uid, "ip_address": ip}
    if error: parsed["error_code"] = error
    return lvl, msg_body(event), raw, parsed

def msg_body(event):
    return f"Keycloak event {event}"

GENERATORS = {"postgres": gen_postgres, "tomcat": gen_tomcat, "keycloak": gen_keycloak}


# --------------------------------------------------------------------------- #
# Construcción del documento enriquecido (estilo Fluentd kubernetes_metadata)
# --------------------------------------------------------------------------- #

def build_doc(service, dt):
    lvl, message, raw, parsed = GENERATORS[service](dt)
    pod = random.choice(TOPOLOGY[service])
    stream = "stderr" if lvl in ("ERROR", "FATAL", "WARN") and random.random() < 0.7 else "stdout"
    k8s = {k: v for k, v in pod.items() if not k.startswith("_")}
    tag = f"kube.var.log.containers.{pod['pod_name']}_{pod['namespace_name']}_{pod['container_name']}-{pod['_docker_id']}.log"
    doc = {
        "@timestamp": dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond//1000:03d}Z",
        "service": service,
        "level": lvl,
        "message": message,
        "log": raw,
        "stream": stream,
        "tag": tag,
        "kubernetes": k8s,
        "docker": {"container_id": pod["_docker_id"]},
        "host": pod["host"],
    }
    doc.update(parsed)
    return doc


# --------------------------------------------------------------------------- #
# Plantilla de índice + creación + alias
# --------------------------------------------------------------------------- #

TEMPLATE = {
    "index_patterns": ["logs-*"],
    "template": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        "aliases": {"logs": {}},
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "service": {"type": "keyword"},
                "level": {"type": "keyword"},
                "message": {"type": "text"},
                "log": {"type": "text"},
                "stream": {"type": "keyword"},
                "tag": {"type": "keyword"},
                "host": {"type": "keyword"},
                "logger": {"type": "keyword"},
                "thread": {"type": "keyword"},
                "kubernetes": {"properties": {
                    "namespace_name": {"type": "keyword"},
                    "pod_name": {"type": "keyword"},
                    "pod_id": {"type": "keyword"},
                    "container_name": {"type": "keyword"},
                    "container_image": {"type": "keyword"},
                    "container_image_id": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "master_url": {"type": "keyword"},
                    "namespace_id": {"type": "keyword"},
                    "labels": {"type": "object"},
                }},
                "docker": {"properties": {"container_id": {"type": "keyword"}}},
                # postgres
                "pg_pid": {"type": "integer"}, "pg_level": {"type": "keyword"},
                "duration_ms": {"type": "float"}, "db_name": {"type": "keyword"}, "db_user": {"type": "keyword"},
                # tomcat
                "exception": {"type": "keyword"}, "status_code": {"type": "keyword"},
                "response_ms": {"type": "integer"}, "request_path": {"type": "keyword"},
                # keycloak
                "kc_event_type": {"type": "keyword"}, "realm": {"type": "keyword"},
                "client_id": {"type": "keyword"}, "user_id": {"type": "keyword"},
                "ip_address": {"type": "ip"}, "error_code": {"type": "keyword"},
            }
        },
    },
}

def setup(os_client, reset):
    if reset:
        for idx in INDEX.values():
            os_client.req("DELETE", "/" + idx)
        print("· índices previos borrados")
    st, _ = os_client.req("PUT", "/_index_template/logs-template", TEMPLATE)
    print(f"· plantilla logs-* -> {st}")
    for idx in INDEX.values():
        st, body = os_client.req("PUT", "/" + idx)
        ok = st < 300 or body.get("error", {}).get("type") == "resource_already_exists_exception"
        print(f"· índice {idx} -> {st} {'(ya existía)' if 'already_exists' in json.dumps(body) else ''}")
    # asegurar alias por si la plantilla no aplicó (índices preexistentes)
    actions = [{"add": {"index": idx, "alias": "logs"}} for idx in INDEX.values()]
    os_client.req("POST", "/_aliases", {"actions": actions})
    print("· alias 'logs' -> apunta a", ", ".join(INDEX.values()))


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #

def bulk_load(os_client, service, docs):
    idx = INDEX[service]
    lines = []
    for d in docs:
        lines.append(json.dumps({"index": {"_index": idx}}))
        lines.append(json.dumps(d, ensure_ascii=False))
    body = "\n".join(lines) + "\n"
    st, resp = os_client.req("POST", "/_bulk", body, ndjson=True)
    if resp.get("errors"):
        first = next((list(i.values())[0] for i in resp["items"] if list(i.values())[0].get("status", 200) >= 300), {})
        raise RuntimeError(f"bulk con errores en {idx}: {first.get('error')}")
    return len(docs)

def initial_load(os_client, n, hours):
    now = datetime.now(timezone.utc)
    for service in INDEX:
        total = 0
        # repartir en lotes de 2000, timestamps en las últimas `hours` horas (sesgo a reciente)
        while total < n:
            batch = min(2000, n - total)
            docs = []
            for _ in range(batch):
                back = (random.random() ** 1.6) * hours * 3600   # sesgo hacia ahora
                docs.append(build_doc(service, now - timedelta(seconds=back)))
            bulk_load(os_client, service, docs)
            total += batch
        os_client.req("POST", f"/{INDEX[service]}/_refresh")
        print(f"· carga inicial {INDEX[service]}: {total} docs")


def live_loop(os_client, rate):
    print(f"\n▶ goteo en vivo: ~{rate}/min por índice. Ctrl+C para parar.\n")
    minute = 0
    try:
        while True:
            time.sleep(60)
            minute += 1
            now = datetime.now(timezone.utc)
            summary = []
            for service in INDEX:
                n = max(0, round(random.gauss(rate, rate * 0.4)))
                if n:
                    docs = [build_doc(service, now - timedelta(seconds=random.randint(0, 59))) for _ in range(n)]
                    bulk_load(os_client, service, docs)
                summary.append(f"{service}:{n}")
            print(f"[min {minute}] {now.strftime('%H:%M:%S')}  +  " + "  ".join(summary), flush=True)
    except KeyboardInterrupt:
        print("\n■ detenido por el usuario.")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    p = argparse.ArgumentParser(description="Simulador de logs k8s (Fluentd) para OpenSearch.")
    p.add_argument("--host", default="https://opensearch.iochannel.tech")
    p.add_argument("--user", default="admin")
    p.add_argument("--password", default="Pa$$w0rd2026")
    p.add_argument("--initial", type=int, default=10000, help="docs iniciales por índice")
    p.add_argument("--rate", type=float, default=5, help="docs/min por índice en vivo")
    p.add_argument("--spread-hours", type=float, default=6, help="horas hacia atrás para los docs iniciales")
    p.add_argument("--reset", action="store_true", help="borrar los índices antes de crear")
    p.add_argument("--no-initial", action="store_true", help="saltar la carga inicial")
    p.add_argument("--no-loop", action="store_true", help="no quedarse en bucle (solo setup+inicial)")
    args = p.parse_args()

    os_client = OS(args.host, args.user, args.password)
    print(f"OpenSearch: {args.host}")
    setup(os_client, args.reset)
    if not args.no_initial:
        initial_load(os_client, args.initial, args.spread_hours)
    if not args.no_loop:
        live_loop(os_client, args.rate)
    print("\nConsulta:  GET logs/_count   ·   GET logs-*/_search   ·   data view logs-*")


if __name__ == "__main__":
    main()
