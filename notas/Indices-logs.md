## Mappings de Postgres
```json
"@timestamp": {
    "type": "date"
},
"client_id": {
    "type": "keyword"
},
"db_name": {
    "type": "keyword"
},
"db_user": {
    "type": "keyword"
},
"docker": {
    "properties": {
    "container_id": {
        "type": "keyword"
    }
    }
},
"duration_ms": {
    "type": "float"
},
"error_code": {
    "type": "keyword"
},
"exception": {
    "type": "keyword"
},
"host": {
    "type": "keyword"
},
"ip_address": {
    "type": "ip"
},
"kc_event_type": {
    "type": "keyword"
},
"kubernetes": {
    "properties": {
        "container_image": {
            "type": "keyword"
        },
        "container_image_id": {
            "type": "keyword"
        },
        "container_name": {
            "type": "keyword"
        },
        "host": {
            "type": "keyword"
        },
        "labels": {
            "properties": {
            "app": {
                "type": "text",
                "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256
                }
                }
            },
            "app_kubernetes_io_name": {
                "type": "text",
                "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256
                }
                }
            },
            "statefulset_kubernetes_io_pod-name": {
                "type": "text",
                "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256
                }
                }
            },
            "tier": {
                "type": "text",
                "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256
                }
                }
            }
        }
    }
    }
}
```


## Ejemplo de postgres
```json
"_source": {
          "@timestamp": "2026-06-30T09:18:47.717Z",
          "service": "postgres",
          "level": "INFO",
          "message": "duration: 670.296 ms  statement: SELECT * FROM products WHERE id = 97266",
          "log": "2026-06-30 09:18:47.717 UTC [2184] LOG:  duration: 670.296 ms  statement: SELECT * FROM products WHERE id = 97266",
          "stream": "stdout",
          "tag": "kube.var.log.containers.postgresql-1_databases_postgres-d8c95361704016d94891488cc7feca9f74b86fdcc376d91e50e1dfce5cc25c50.log",
          "kubernetes": {
            "namespace_name": "databases",
            "pod_name": "postgresql-1",
            "pod_id": "fc824760-e21f-5ff4-1b17-85d4d8e72085",
            "container_name": "postgres",
            "container_image": "postgres:16.2",
            "container_image_id": "docker-pullable://postgres@sha256:41c4cdd8c00faeb7fe6dbd9b67e636e474a298527b0b1d635ad858312627049c",
            "host": "ip-10-0-2-47.eu-west-1.compute.internal",
            "labels": {
              "app": "postgresql",
              "app_kubernetes_io_name": "postgresql",
              "tier": "db",
              "statefulset_kubernetes_io_pod-name": "postgresql"
            },
            "master_url": "https://10.96.0.1:443/api",
            "namespace_id": "8e617076-0721-fc36-aa8c-32e5d8d7b0bf"
          },
          "docker": {
            "container_id": "d8c95361704016d94891488cc7feca9f74b86fdcc376d91e50e1dfce5cc25c50"
          },
          "host": "ip-10-0-2-47.eu-west-1.compute.internal",
          "pg_pid": 2184,
          "pg_level": "LOG",
          "db_name": "facturacion",
          "db_user": "reporting",
          "logger": "postgres",
          "duration_ms": 670.296
        }
```

2026-06-30 09:18:47.717 UTC [2184] LOG:  duration: 670.296 ms  statement: SELECT * FROM products WHERE id = 97266


SELECT * FROM products WHERE id = 97266
INSERT
UPDATE
DELETE

---
CRUD         TABLAS

CUANTITATIVA DURACION
CUALITATIVA  OPERACION
CULITATIVA   TABLA

HEATMAP

            INSERT  UPDATE   DELETE     SELECT
    Tabla1   ???                                        Número total de queries (COUNT) por tabla y por operación
    Tabla2                                              AVG duración de queries por tabla y por operación
    Tabla3
    TablaN

    Las tablas/operaciones más calientes
    Las tablas/operaciones más lentas

Puedo hacerla? NO puedo..Sería genial.. pero no puedo!
Tengo indexados esos campos? OPERACION / TABLA? NO... pues no hay forma.


message "duration: 670.296 ms  statement: SELECT * FROM products WHERE id = 97266"

De ese campo querria extraer, igual que he extraído el duration_ms, la operación y la tabla.
¿Cómo se haría eso?
--> "table" y "operation"

FluentD o mejor aún DataPepper
No es algo que arregle ni siquiera con un analizador sintáctico.
    Filtro grok
Esto es INGESTA de datos.


CARGO DATOS ---> Planteo dashboards

Planteo dashboards  -> Cargo datos que me permitan generar esos dashboards.

    Número de eventos (Frecuencia)
    ^
    |
    |
    +----------> tiempo

    Separado por tipo de servicio

---

Histograma de errores o fatal por servicio.