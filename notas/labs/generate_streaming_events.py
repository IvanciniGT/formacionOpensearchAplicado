#!/usr/bin/env python3
"""
Generador de datos sintéticos para el laboratorio de OpenSearch Dashboards.

Caso: plataforma de streaming / CDN / observabilidad de reproducción.
Produce un fichero NDJSON listo para la API _bulk de OpenSearch, con eventos
realistas (tráfico no uniforme, geografía, dispositivos, latencias) y 3
incidentes inyectados claramente visibles en dashboards.

Uso:
    python3 generate_streaming_events.py \
        --docs 100000 \
        --index streaming-events-ivan \
        --output streaming-events.bulk.ndjson

Sin dependencias externas: solo librería estándar de Python 3.
"""

import argparse
import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------------- #
# Catálogos de datos
# --------------------------------------------------------------------------- #

# Ciudades con coordenadas reales y peso de tráfico (España con más peso).
CITIES = [
    # city,         region,           country,          cc,    lat,      lon,     peso, lat_off, err_bias
    ("Madrid",       "Madrid",         "Spain",          "ES",  40.4168,  -3.7038,  22,   0,    1.0),
    ("Barcelona",    "Catalonia",      "Spain",          "ES",  41.3874,   2.1686,  16,   0,    1.0),
    ("Valencia",     "Valencia",       "Spain",          "ES",  39.4699,  -0.3763,   6,  10,    1.0),
    ("Sevilla",      "Andalusia",      "Spain",          "ES",  37.3891,  -5.9845,   5,  20,    1.0),
    ("Bilbao",       "Basque Country", "Spain",          "ES",  43.2630,  -2.9350,   4,  15,    1.0),
    ("Málaga",       "Andalusia",      "Spain",          "ES",  36.7213,  -4.4214,   3,  25,    1.0),
    ("Lisboa",       "Lisbon",         "Portugal",       "PT",  38.7223,  -9.1393,   3,  30,    1.1),
    ("Paris",        "Île-de-France",  "France",         "FR",  48.8566,   2.3522,   6,  20,    1.0),
    ("London",       "England",        "United Kingdom", "GB",  51.5072,  -0.1276,   7,  20,    1.0),
    ("Berlin",       "Berlin",         "Germany",        "DE",  52.5200,  13.4050,   5,  25,    1.0),
    ("Rome",         "Lazio",          "Italy",          "IT",  41.9028,  12.4964,   4,  35,    1.1),
    ("Amsterdam",    "North Holland",  "Netherlands",    "NL",  52.3676,   4.9041,   3,  20,    1.0),
    ("New York",     "New York",       "United States",  "US",  40.7128, -74.0060,   5,  60,    1.2),
    ("Miami",        "Florida",        "United States",  "US",  25.7617, -80.1918,   3,  70,    1.2),
    ("Mexico City",  "Mexico City",    "Mexico",         "MX",  19.4326, -99.1332,   5, 120,    1.3),
    ("Buenos Aires", "Buenos Aires",   "Argentina",      "AR", -34.6037, -58.3816,   4, 150,    1.3),
]
CITY_WEIGHTS = [c[6] for c in CITIES]

# Código de edge por ciudad (para edge_node).
CITY_EDGE = {
    "Madrid": "mad", "Barcelona": "bcn", "Valencia": "vlc", "Sevilla": "svq",
    "Bilbao": "bio", "Málaga": "agp", "Lisboa": "lis", "Paris": "par",
    "London": "lon", "Berlin": "ber", "Rome": "rom", "Amsterdam": "ams",
    "New York": "nyc", "Miami": "mia", "Mexico City": "mex", "Buenos Aires": "bue",
}

SERVICES = [
    ("cdn-edge", 18), ("player-api", 16), ("analytics-ingest", 13),
    ("catalog-api", 12), ("user-profile-api", 10), ("recommendation-api", 8),
    ("auth-service", 8), ("search-api", 8), ("drm-service", 7),
]
SERVICE_NAMES = [s[0] for s in SERVICES]
SERVICE_WEIGHTS = [s[1] for s in SERVICES]
# 4-6 hosts por servicio => >30 hosts en total.
HOSTS = {s: [f"{s}-{i:02d}" for i in range(1, random.randint(4, 6) + 1)] for s in SERVICE_NAMES}

ENVIRONMENTS = (["prod"] * 85) + (["pre"] * 8) + (["test"] * 5) + (["dev"] * 2)

EVENT_TYPES = [
    ("segment_request", 30), ("heartbeat", 20), ("api_request", 18),
    ("playback_start", 7), ("playback_stop", 6), ("buffering", 5),
    ("search", 4), ("content_detail", 4), ("login", 3),
    ("playback_error", 2), ("recommendation_request", 1),
]
EVENT_NAMES = [e[0] for e in EVENT_TYPES]
EVENT_WEIGHTS = [e[1] for e in EVENT_TYPES]

DEVICES = [
    ("Mobile", 34, ["Android", "Android", "iOS", "iOS"]),
    ("Smart TV", 24, ["Tizen", "Tizen", "webOS", "webOS", "Android"]),
    ("Web", 18, ["Windows", "Windows", "macOS", "Linux"]),
    ("Tablet", 10, ["iPadOS", "iPadOS", "Android"]),
    ("Console", 8, ["PlayStation OS", "Xbox OS"]),
    ("Set-top Box", 6, ["Android", "Linux"]),
]
DEVICE_NAMES = [d[0] for d in DEVICES]
DEVICE_WEIGHTS = [d[1] for d in DEVICES]
DEVICE_OS = {d[0]: d[2] for d in DEVICES}

USER_PLANS = (["free"] * 25) + (["basic"] * 25) + (["standard"] * 25) + \
             (["premium"] * 17) + (["family"] * 8)

ISPS = [
    ("Movistar", 22), ("Vodafone", 16), ("Orange", 14), ("MasMovil", 8),
    ("Jazztel", 5), ("Deutsche Telekom", 6), ("BT", 6), ("Free SAS", 5),
    ("Comcast", 6), ("AT&T", 5), ("Telmex", 4), ("SlowNet Telecom", 7),
]
ISP_NAMES = [i[0] for i in ISPS]
ISP_WEIGHTS = [i[1] for i in ISPS]
# ISP con peor calidad (más latencia/errores) para crear diferencias.
ISP_BAD = "SlowNet Telecom"

CDN_PROVIDERS = ["Akamai", "CloudFront", "Fastly", "Cloudflare", "Internal-CDN"]

CONTENT_TYPES = [("movie", 30), ("series", 35), ("live", 12),
                 ("documentary", 10), ("sports", 13)]
CT_NAMES = [c[0] for c in CONTENT_TYPES]
CT_WEIGHTS = [c[1] for c in CONTENT_TYPES]

GENRES = ["thriller", "comedy", "drama", "sci-fi", "documentary",
          "sports", "kids", "action", "crime", "reality"]

CONTENT_TITLES = [
    "La sombra del nodo", "Código de medianoche", "El último despliegue",
    "Latency City", "The Broken Cache", "Horizonte Azul", "Distrito Kafka",
    "The Silent Shard", "Operación Bitrate", "La frontera del CDN",
    "Reinas del streaming", "El protocolo Helena", "Niebla en el datacenter",
    "Cazadores de paquetes", "La red invisible", "Tormenta de tokens",
    "El algoritmo perdido", "Memorias de un sysadmin", "La gran caída",
    "Pulso digital", "Crónicas del kernel", "El jardín de los logs",
    "Frecuencia rota", "La hora del rollback", "Sombras en la nube",
    "Edge of Tomorrow Night", "The Throughput", "Midnight Packets",
    "Cold Storage", "The Latency Game", "Bytes & Beasts", "Final Commit",
    "Origin Story", "The Cache Whisperer", "Downtime", "Bandwidth Heist",
    "Cumbre de servidores", "El testigo del firewall", "Latidos de fibra",
    "La conjura de los proxies", "Maratón de medianoche", "Rumbo al exabyte",
    "El silencio del buffer", "Días de paquetes perdidos", "La señal",
    "Anatomía de un fallo", "El despertar del clúster", "Vértigo de red",
    "Los guardianes del uptime", "Eclipse de servicio", "Resolución 4K",
    "El mapa del tráfico", "Fronteras de banda ancha", "El relevo del nodo",
    "Saga del streaming", "Réplica fantasma", "Cero absoluto",
    "La temporada de los errores", "Punto de no retorno", "Última conexión",
]

APP_VERSIONS = (["4.12.3"] * 30) + (["4.12.1"] * 20) + (["4.11.7"] * 20) + \
               (["4.13.0-beta"] * 10) + (["3.9.4"] * 20)

API_ENDPOINTS = {
    "player-api": ["/v1/playback/start", "/v1/playback/heartbeat", "/v1/playback/stop"],
    "catalog-api": ["/v1/catalog", "/v1/catalog/detail", "/v1/catalog/browse"],
    "recommendation-api": ["/v1/recommendations", "/v1/recommendations/home", "/v1/recommendations/similar"],
    "auth-service": ["/v1/auth/login", "/v1/auth/refresh", "/v1/auth/logout"],
    "drm-service": ["/v1/drm/license", "/v1/drm/cert"],
    "search-api": ["/v1/search", "/v1/search/suggest"],
    "cdn-edge": ["/segments/video", "/segments/audio", "/manifest.mpd"],
    "analytics-ingest": ["/v1/events", "/v1/metrics"],
    "user-profile-api": ["/v1/profile", "/v1/profile/watchlist", "/v1/profile/settings"],
}

USER_AGENTS = {
    "Mobile": "StreamApp/4.12 (Mobile; %s)",
    "Smart TV": "StreamApp/4.12 (SmartTV; %s)",
    "Tablet": "StreamApp/4.12 (Tablet; %s)",
    "Web": "Mozilla/5.0 (%s) StreamWeb/4.12",
    "Console": "StreamApp/4.12 (Console; %s)",
    "Set-top Box": "StreamApp/4.12 (STB; %s)",
}

STATUS_OK = [200, 200, 200, 200, 201, 204]
STATUS_WARN = [400, 401, 403, 404, 408, 429]
STATUS_ERROR = [500, 502, 503, 504]

ERROR_CODES_WARN = ["AUTH_FAILED", "RATE_LIMITED", "SEGMENT_NOT_FOUND",
                    "VIDEO_MANIFEST_ERROR", "BUFFERING_SPIKE", "SEARCH_TIMEOUT",
                    "DRM_LICENSE_ERROR", "PLAYBACK_START_FAILED"]
ERROR_CODES_ERROR = ["CDN_TIMEOUT", "ORIGIN_TIMEOUT", "SERVICE_UNAVAILABLE",
                     "DRM_LICENSE_ERROR", "VIDEO_MANIFEST_ERROR",
                     "PLAYBACK_START_FAILED", "UNKNOWN_ERROR"]

MESSAGES_BY_ERROR = {
    "CDN_TIMEOUT": "Timeout while fetching segment from CDN edge node",
    "ORIGIN_TIMEOUT": "Origin server timed out",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "AUTH_FAILED": "Authentication failed for user",
    "DRM_LICENSE_ERROR": "DRM license validation failed",
    "VIDEO_MANIFEST_ERROR": "Failed to parse video manifest",
    "SEGMENT_NOT_FOUND": "Requested media segment not found",
    "RATE_LIMITED": "Request rate limited",
    "BUFFERING_SPIKE": "High buffering detected on client",
    "PLAYBACK_START_FAILED": "Playback failed to start",
    "SEARCH_TIMEOUT": "Search request timed out",
    "UNKNOWN_ERROR": "Unexpected error occurred",
}
MESSAGES_BY_EVENT = {
    "playback_start": "Playback started successfully",
    "playback_stop": "Playback stopped by user",
    "segment_request": "Segment delivered from CDN cache",
    "api_request": "API request completed",
    "search": "Search request completed",
    "login": "User login successful",
    "heartbeat": "Playback heartbeat received",
    "buffering": "High buffering detected on client",
    "content_detail": "Content detail loaded",
    "recommendation_request": "Recommendations generated",
    "playback_stop_origin": "Segment fetched from origin",
}

# Pools de identidades para que haya repetición (sesiones / usuarios recurrentes).
USER_POOL = [f"u_{uuid.UUID(int=random.getrandbits(128)).hex[:12]}" for _ in range(5000)]
SESSION_POOL = [f"s_{uuid.UUID(int=random.getrandbits(128)).hex[:12]}" for _ in range(20000)]
CONTENT_IDS = [f"c_{1000 + i}" for i in range(200)]


# --------------------------------------------------------------------------- #
# Utilidades temporales
# --------------------------------------------------------------------------- #

# Pesos por hora del día (UTC): pico 19:00-23:30, valle 02:00-07:00.
HOUR_WEIGHTS = [
    4, 3, 2, 2, 2, 2, 3, 4,   # 00-07
    6, 8, 9, 10, 11, 10, 9, 9,  # 08-15
    11, 13, 16, 22, 24, 23, 20, 12,  # 16-23
]
# Pesos por día de la semana (lun=0 ... dom=6): viernes/sábado/domingo más.
DOW_WEIGHTS = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.1, 4: 1.4, 5: 1.7, 6: 1.6}


def random_timestamp(now, days=14):
    """Devuelve un datetime UTC en los últimos `days` días, no uniforme."""
    # Elegir día por peso de día de la semana.
    day_choices = list(range(days))
    day_weights = []
    for d in day_choices:
        dt = now - timedelta(days=d)
        day_weights.append(DOW_WEIGHTS.get(dt.weekday(), 1.0))
    day_offset = random.choices(day_choices, weights=day_weights, k=1)[0]
    base = now - timedelta(days=day_offset)
    hour = random.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]
    dt = base.replace(hour=hour, minute=random.randint(0, 59),
                      second=random.randint(0, 59),
                      microsecond=random.randint(0, 999) * 1000)
    if dt > now:                      # no generamos futuro
        dt -= timedelta(days=1)
    return dt


def iso_z(dt):
    """ISO8601 con milisegundos y sufijo Z (UTC)."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


# --------------------------------------------------------------------------- #
# Generación de un documento
# --------------------------------------------------------------------------- #

def pick_city():
    return random.choices(CITIES, weights=CITY_WEIGHTS, k=1)[0]


def make_geo(city):
    lat = city[4] + random.uniform(-0.06, 0.06)
    lon = city[5] + random.uniform(-0.06, 0.06)
    return {"location": {"lat": round(lat, 4), "lon": round(lon, 4)}}


def base_document(now, dt):
    """Documento 'normal' (no perteneciente a un incidente)."""
    city = pick_city()
    device = random.choices(DEVICE_NAMES, weights=DEVICE_WEIGHTS, k=1)[0]
    os_name = random.choice(DEVICE_OS[device])
    service = random.choices(SERVICE_NAMES, weights=SERVICE_WEIGHTS, k=1)[0]
    event_type = random.choices(EVENT_NAMES, weights=EVENT_WEIGHTS, k=1)[0]
    isp = random.choices(ISP_NAMES, weights=ISP_WEIGHTS, k=1)[0]
    plan = random.choice(USER_PLANS)

    # Nivel (con sesgo del ISP malo hacia más WARN/ERROR).
    if isp == ISP_BAD:
        level = random.choices(["INFO", "WARN", "ERROR"], weights=[60, 25, 15], k=1)[0]
    else:
        level = random.choices(["INFO", "WARN", "ERROR"], weights=[75, 17, 8], k=1)[0]

    return build_event(now, dt, city, device, os_name, service, event_type,
                       isp, plan, level)


def build_event(now, dt, city, device, os_name, service, event_type, isp,
                plan, level, status=None, error_code=None, latency=None,
                cache_hit=None, buffering=None, message=None):
    """Construye el documento aplicando todas las reglas de coherencia."""
    cityname, region, country, cc, _, _, _, lat_off, err_bias = city

    # --- status_code coherente con el nivel ---
    if status is None:
        if level == "INFO":
            status = random.choice(STATUS_OK)
        elif level == "WARN":
            status = random.choice(STATUS_WARN)
        else:
            status = random.choice(STATUS_ERROR)
    status = str(status)

    is_error = (level == "ERROR") or (int(status) >= 500)

    # --- error_code: ausente en eventos normales (INFO), presente en WARN/ERROR ---
    if error_code is None and level != "INFO":
        error_code = random.choice(ERROR_CODES_WARN if level == "WARN"
                                   else ERROR_CODES_ERROR)

    # --- latencia coherente con el nivel + offset de ciudad / ISP ---
    if latency is None:
        if level == "INFO":
            latency = int(random.triangular(40, 350, 120))
        elif level == "WARN":
            latency = int(random.triangular(300, 1200, 600))
        else:
            latency = int(random.triangular(800, 5000, 1800))
        latency += int(lat_off)
        if isp == ISP_BAD:
            latency = int(latency * random.uniform(1.3, 1.9))
    latency = max(5, latency)

    # --- buffering / rebuffer ---
    if buffering is None:
        if event_type == "buffering" or error_code == "BUFFERING_SPIKE":
            buffering = random.randint(800, 12000)
        elif random.random() < 0.12:
            buffering = random.randint(100, 1500)
        else:
            buffering = 0
    rebuffer = 0 if buffering == 0 else random.randint(1, 8)

    # --- cache_hit ---
    if cache_hit is None:
        cache_hit = random.random() < 0.80

    # --- bytes / bitrate / duración ---
    bitrate = random.choices([800, 1200, 2500, 4500, 8000, 12000],
                             weights=[6, 12, 22, 26, 22, 12], k=1)[0]
    content_type = random.choices(CT_NAMES, weights=CT_WEIGHTS, k=1)[0]
    if event_type == "segment_request":
        bytes_sent = random.randint(50_000, 2_000_000)
    elif event_type in ("playback_start", "playback_stop"):
        bytes_sent = random.randint(1_000_000, 20_000_000)
    elif event_type == "heartbeat":
        bytes_sent = random.randint(500, 5_000)
    elif event_type == "buffering":
        bytes_sent = random.randint(10_000, 200_000)
    else:
        bytes_sent = random.randint(1_000, 60_000)
    if content_type in ("live", "sports"):
        bytes_sent = int(bytes_sent * random.uniform(1.5, 3.0))

    if event_type in ("playback_start", "playback_stop"):
        duration = random.randint(60_000, 7_200_000)
    elif event_type == "buffering":
        duration = buffering
    else:
        duration = random.randint(50, 2_000)

    # --- cliente ---
    cpu = round(min(99.0, max(1.0, random.gauss(35, 16))), 1)
    if device in ("Mobile", "Tablet"):
        memory = random.randint(200, 1500)
    elif device == "Smart TV":
        memory = random.randint(400, 2500)
    else:
        memory = random.randint(800, 8000)

    # --- mensaje ---
    if message is None:
        if error_code:
            message = MESSAGES_BY_ERROR.get(error_code, "Unexpected error occurred")
        elif event_type == "segment_request" and not cache_hit:
            message = MESSAGES_BY_EVENT["playback_stop_origin"]
        else:
            message = MESSAGES_BY_EVENT.get(event_type, "Event processed")

    host = random.choice(HOSTS[service])
    endpoint = random.choice(API_ENDPOINTS[service])
    method = "POST" if event_type in ("login", "search", "playback_start",
                                      "recommendation_request") else "GET"
    edge = f"{CITY_EDGE[cityname]}-edge-{random.randint(1, 3):02d}"

    doc = {
        "@timestamp": iso_z(dt),
        "event_id": str(uuid.UUID(int=random.getrandbits(128))),
        "event_type": event_type,
        "service": service,
        "environment": random.choice(ENVIRONMENTS),
        "host": host,
        "level": level,
        "status_code": status,
        "country": country,
        "country_code": cc,
        "region": region,
        "city": cityname,
        "geo": make_geo(city),
        "device_type": device,
        "os": os_name,
        "app_version": random.choice(APP_VERSIONS),
        "user_plan": plan,
        "is_premium": plan in ("premium", "family"),
        "isp": isp,
        "content_id": random.choice(CONTENT_IDS),
        "content_type": content_type,
        "content_title": random.choice(CONTENT_TITLES),
        "genre": random.choice(GENRES),
        "cdn_provider": random.choice(CDN_PROVIDERS),
        "edge_node": edge,
        "request_method": method,
        "api_endpoint": endpoint,
        "session_id": random.choice(SESSION_POOL),
        "user_id": random.choice(USER_POOL),
        "latency_ms": latency,
        "duration_ms": duration,
        "bytes_sent": bytes_sent,
        "bitrate_kbps": bitrate,
        "buffering_ms": buffering,
        "rebuffer_count": rebuffer,
        "cpu_client_pct": cpu,
        "memory_client_mb": memory,
        "cache_hit": cache_hit,
        "is_error": is_error,
        "message": message,
        "user_agent": USER_AGENTS[device] % os_name,
    }
    if error_code:
        doc["error_code"] = error_code
    return doc


# --------------------------------------------------------------------------- #
# Incidentes
# --------------------------------------------------------------------------- #

def incident1_doc(now, win):
    """CDN timeout geográfico: Madrid/Barcelona, cdn-edge, 504, CDN_TIMEOUT."""
    dt = win[0] + (win[1] - win[0]) * random.random()
    target = random.choices(["Madrid", "Barcelona", "Valencia"],
                            weights=[55, 35, 10], k=1)[0]
    city = next(c for c in CITIES if c[0] == target)
    device = random.choices(DEVICE_NAMES, weights=DEVICE_WEIGHTS, k=1)[0]
    level = random.choices(["ERROR", "WARN"], weights=[80, 20], k=1)[0]
    return build_event(
        now, dt, city, device, random.choice(DEVICE_OS[device]), "cdn-edge",
        random.choices(["segment_request", "playback_error"], weights=[70, 30], k=1)[0],
        random.choices(ISP_NAMES, weights=ISP_WEIGHTS, k=1)[0], random.choice(USER_PLANS),
        level, status=504, error_code="CDN_TIMEOUT",
        latency=random.randint(2000, 8000), cache_hit=False,
        message="Timeout while fetching segment from CDN edge node")


def incident2_doc(now, win):
    """Latencia alta en Smart TV, sobre todo player-api; p95/p99 visibles."""
    dt = win[0] + (win[1] - win[0]) * random.random()
    city = pick_city()
    service = random.choices(["player-api", "cdn-edge", "catalog-api"],
                             weights=[70, 18, 12], k=1)[0]
    # Mayoría INFO pero MUY lentos (mancha el p95/p99), parte WARN/ERROR.
    level = random.choices(["INFO", "WARN", "ERROR"], weights=[55, 30, 15], k=1)[0]
    status = None
    if level == "INFO":
        status = 200
    return build_event(
        now, dt, city, "Smart TV", random.choice(["Tizen", "webOS"]),
        service, random.choices(["playback_start", "segment_request", "buffering"],
                                weights=[40, 40, 20], k=1)[0],
        random.choices(ISP_NAMES, weights=ISP_WEIGHTS, k=1)[0], random.choice(USER_PLANS),
        level, status=status,
        latency=random.randint(2500, 9000),
        buffering=random.randint(1500, 14000),
        message="High latency detected on Smart TV playback")


def incident3_doc(now, win):
    """Recommendation API degradada: 503 + SERVICE_UNAVAILABLE."""
    dt = win[0] + (win[1] - win[0]) * random.random()
    city = pick_city()
    device = random.choices(DEVICE_NAMES, weights=DEVICE_WEIGHTS, k=1)[0]
    return build_event(
        now, dt, city, device, random.choice(DEVICE_OS[device]),
        "recommendation-api",
        random.choices(["recommendation_request", "api_request"], weights=[70, 30], k=1)[0],
        random.choices(ISP_NAMES, weights=ISP_WEIGHTS, k=1)[0], random.choice(USER_PLANS),
        "ERROR", status=503, error_code="SERVICE_UNAVAILABLE",
        latency=random.randint(1500, 6000), cache_hit=False,
        message="Recommendation service unavailable")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Generador de eventos de streaming sintéticos.")
    parser.add_argument("--docs", type=int, default=100000, help="número de documentos")
    parser.add_argument("--index", default="streaming-events-ivan", help="nombre del índice")
    parser.add_argument("--output", default="streaming-events.bulk.ndjson", help="fichero NDJSON de salida")
    parser.add_argument("--seed", type=int, default=42, help="semilla para reproducibilidad")
    args = parser.parse_args()

    random.seed(args.seed)
    now = datetime.now(timezone.utc)

    # Ventanas de incidente (anclas en franja de tarde/noche para que se vean).
    inc1 = ((now - timedelta(days=10)).replace(hour=20, minute=0, second=0, microsecond=0),)
    inc1 = (inc1[0], inc1[0] + timedelta(hours=2))
    inc2 = ((now - timedelta(days=6)).replace(hour=18, minute=0, second=0, microsecond=0),)
    inc2 = (inc2[0], inc2[0] + timedelta(hours=4))
    inc3 = ((now - timedelta(days=2)).replace(hour=21, minute=0, second=0, microsecond=0),)
    inc3 = (inc3[0], inc3[0] + timedelta(minutes=45))

    # Reparto de documentos: ~8.5% a incidentes, resto normales.
    n_inc1 = int(args.docs * 0.030)
    n_inc2 = int(args.docs * 0.040)
    n_inc3 = int(args.docs * 0.015)
    n_base = args.docs - n_inc1 - n_inc2 - n_inc3

    min_dt = now
    max_dt = now - timedelta(days=30)
    action_tmpl = '{{"index":{{"_index":"{idx}","_id":"{id}"}}}}'

    written = 0
    with open(args.output, "w", encoding="utf-8") as f:
        def emit(doc):
            nonlocal written, min_dt, max_dt
            f.write(action_tmpl.format(idx=args.index, id=doc["event_id"]))
            f.write("\n")
            f.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")
            written += 1
            ts = doc["@timestamp"]
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            min_dt = min(min_dt, dt)
            max_dt = max(max_dt, dt)

        for _ in range(n_base):
            emit(base_document(now, random_timestamp(now)))
        for _ in range(n_inc1):
            emit(incident1_doc(now, inc1))
        for _ in range(n_inc2):
            emit(incident2_doc(now, inc2))
        for _ in range(n_inc3):
            emit(incident3_doc(now, inc3))

    size = os.path.getsize(args.output)
    print("=" * 60)
    print(f"Documentos generados : {written:,}")
    print(f"  - base             : {n_base:,}")
    print(f"  - incidente 1 (CDN) : {n_inc1:,}  [{iso_z(inc1[0])} .. {iso_z(inc1[1])}]")
    print(f"  - incidente 2 (TV)  : {n_inc2:,}  [{iso_z(inc2[0])} .. {iso_z(inc2[1])}]")
    print(f"  - incidente 3 (reco): {n_inc3:,}  [{iso_z(inc3[0])} .. {iso_z(inc3[1])}]")
    print(f"Índice               : {args.index}")
    print(f"Fichero              : {os.path.abspath(args.output)}")
    print(f"Tamaño               : {size / 1_048_576:.1f} MB")
    print(f"Rango temporal       : {iso_z(min_dt)}  ..  {iso_z(max_dt)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
