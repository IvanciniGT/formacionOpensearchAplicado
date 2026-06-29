# Lab — Usuarios, Roles y Tenants (contenido 10)

Plugin: **opensearch-security** (instalado). Gestiona quién entra, qué puede ver/hacer y dónde
guarda sus dashboards. Interfaz: **☰ → Security**.

> ⚠️ **Clúster compartido:** crear usuarios/roles reales afecta a todos. En clase, **muéstralo**
> con un usuario de demo (`demo_lectura`) y bórralo al final. No toques `admin` ni roles del sistema.

---

## 0. El modelo mental de seguridad

```text
USUARIO          → quién se autentica (interno o vía LDAP/SAML/OIDC)
ROL              → conjunto de PERMISOS (qué clúster/índices/acciones + qué tenants)
ROLE MAPPING     → une USUARIOS (o grupos/backend roles) ↔ ROLES
TENANT           → espacio aislado donde se guardan los SAVED OBJECTS (dashboards, viz...)
```

Idea clave: **un usuario no tiene permisos directamente**. Tiene **roles**, y el role mapping dice
qué usuarios llevan qué roles. Un rol define 3 cosas:
1. **Cluster permissions** (acciones globales).
2. **Index permissions** (sobre qué índices y qué puede hacer: leer, escribir...).
3. **Tenant permissions** (a qué tenants accede y si en lectura o lectura/escritura).

---

## GUI — Security en Dashboards (la vía habitual)

> En el día a día **casi todo esto se hace por interfaz**, no por API. La API (apartados 1–7 de
> abajo) es el equivalente exacto para automatizar o para Dev Tools, pero en clase enséñalo aquí.

**Dónde:** ☰ (menú) → **Security**. Verás estas secciones:

```text
Security
├─ Authentication and authorization  → cómo se autentica (interno, LDAP, SAML, OIDC)
├─ Roles            → crear/editar ROLES (permisos de clúster, índice, tenant; DLS/FLS)
├─ Internal users   → crear/editar USUARIOS internos y su contraseña
├─ Role mappings    → unir USUARIOS / backend roles ↔ ROLES
├─ Tenants          → crear TENANTS (espacios de dashboards)
├─ Permissions      → action groups (grupos de permisos predefinidos)
└─ Audit logs       → registro de accesos (si está habilitado)
```

**Flujo típico por GUI (crear un lector de streaming):**

1. **Roles → Create role** → nombre `streaming_lector`.
   - *Cluster permissions*: `cluster_composite_ops_ro`.
   - *Index permissions*: index pattern `streaming-events-*` → action group `read` (+ `search`).
     - (opcional) *Document level security*: `{ "term": { "country_code": "ES" } }`.
     - (opcional) *Field level security*: excluir `user_id`, `session_id`.
   - *Tenant permissions*: tenant `global` → **Read only**.
   - **Create**.
2. **Internal users → Create internal user** → `demo_lectura`, contraseña, (opcional) backend role.
3. **Role mappings → `streaming_lector` → Map user** → añade `demo_lectura` → **Map**.
4. **Tenants → Create tenant** → `analistas` (si quieres un espacio de equipo).
5. Comprobar: cierra sesión y entra como `demo_lectura` → solo verá `streaming-events-*` y solo lectura.

**Cambiar de tenant (cualquier usuario):** arriba a la derecha (avatar) → **Switch tenants** →
elige Global / Private / `analistas`. Lo que guardes (dashboards, viz) va a ese tenant.

> Regla de oro para la clase: **Roles** (qué se puede) → **Internal users** (quién) →
> **Role mappings** (unir los dos). Sin el mapping, el rol no se aplica a nadie.

A continuación, lo mismo **por API** (Dev Tools) — útil para automatizar o si no quieres salir de
la consola.

---

## 1. Permisos a nivel de índice (lo más importante para usuarios)

Ejemplo: un rol que **solo puede leer** los índices `streaming-events-*` y nada más.

```
PUT _plugins/_security/api/roles/streaming_lector
{
  "cluster_permissions": ["cluster_composite_ops_ro"],
  "index_permissions": [{
    "index_patterns": ["streaming-events-*"],
    "allowed_actions": ["read", "search", "indices:data/read/*", "indices_monitor"]
  }],
  "tenant_permissions": [{
    "tenant_patterns": ["global_tenant"],
    "allowed_actions": ["kibana_all_read"]
  }]
}
```

Un rol de **analista** que además puede escribir en su índice de trabajo:

```
PUT _plugins/_security/api/roles/streaming_analista
{
  "cluster_permissions": ["cluster_composite_ops"],
  "index_permissions": [
    { "index_patterns": ["streaming-events-*"], "allowed_actions": ["read", "search"] },
    { "index_patterns": ["scratch-*"],          "allowed_actions": ["crud", "create_index"] }
  ],
  "tenant_permissions": [
    { "tenant_patterns": ["analistas"], "allowed_actions": ["kibana_all_write"] }
  ]
}
```

> `read`, `crud`, `search`, `create_index` son **action groups** (grupos de permisos predefinidos).
> Es mejor usarlos que listar acciones sueltas.

---

## 2. Crear un usuario interno

```
PUT _plugins/_security/api/internalusers/demo_lectura
{
  "password": "Demo$Pa55w0rd",
  "backend_roles": ["analistas"],
  "attributes": { "departamento": "operaciones" }
}
```

> `backend_roles` son "etiquetas" del usuario (vienen de LDAP en real). Sirven para mapear roles
> por grupo en vez de uno a uno.

---

## 3. Role mapping — unir usuario ↔ rol

```
PUT _plugins/_security/api/rolesmapping/streaming_lector
{
  "users": ["demo_lectura"],
  "backend_roles": ["analistas"]
}
```

Esto da el rol `streaming_lector` a `demo_lectura` (por nombre) y a cualquiera con el backend role
`analistas`. **Sin role mapping, un rol no se aplica a nadie.**

---

## 4. Seguridad a nivel de documento y campo (DLS/FLS)

Más fino que "lee este índice": "lee este índice **pero solo ciertos documentos / sin ciertos campos**".

**Document Level Security** — que un rol solo vea eventos de España:

```
PUT _plugins/_security/api/roles/streaming_espana
{
  "index_permissions": [{
    "index_patterns": ["streaming-events-*"],
    "dls": "{ \"term\": { \"country_code\": \"ES\" } }",
    "allowed_actions": ["read", "search"]
  }]
}
```

**Field Level Security** — ocultar campos sensibles (ej. `user_id`, `session_id`):

```
PUT _plugins/_security/api/roles/streaming_anonimo
{
  "index_permissions": [{
    "index_patterns": ["streaming-events-*"],
    "fls": ["~user_id", "~session_id"],
    "allowed_actions": ["read", "search"]
  }]
}
```
> `~campo` = excluir ese campo. Sin `~`, sería lista blanca (solo esos campos).

---

## 5. Tenants — separar dashboards por equipo

Un **tenant** es un espacio donde viven los *saved objects*. Por defecto hay:

```text
Global   → compartido por todos (lo que se guarda aquí lo ve todo el mundo)
Private  → privado de cada usuario (solo lo ve él)
```

Y puedes crear tenants propios por equipo:

```
PUT _plugins/_security/api/tenants/analistas
{ "description": "Dashboards del equipo de analistas" }
```

Cómo se usa en la interfaz: arriba a la derecha (avatar) → **Switch tenants** → eliges en cuál
trabajas. Lo que guardes (dashboards, visualizaciones) va a ese tenant.

> **Esto resuelve justo lo de la clase:** en vez de prefijar dashboards con el nombre en el tenant
> Global, cada alumno/equipo trabaja en **su tenant** y no se ve el de los demás. Un rol controla
> a qué tenants accede y si en lectura (`kibana_all_read`) o lectura/escritura (`kibana_all_write`).

Impacto en visibilidad de dashboards:
```text
- Dashboard en tenant Global    → lo ven todos los que tengan acceso al Global.
- Dashboard en tenant Private   → solo su autor.
- Dashboard en tenant "analistas" → solo quien tenga ese tenant en su rol.
```

---

## 6. Ver lo que ya existe (sin tocar nada)

```
GET _plugins/_security/api/roles                 # todos los roles
GET _plugins/_security/api/roles/streaming_lector
GET _plugins/_security/api/internalusers         # usuarios internos
GET _plugins/_security/api/rolesmapping          # mapeos
GET _plugins/_security/api/tenants               # tenants
GET _plugins/_security/authinfo                  # ¿quién soy yo y qué roles tengo?
```

> `GET _plugins/_security/api/authinfo` es genial para clase: muestra tu usuario, tus roles,
> backend roles y tenants. "Esto es lo que el sistema sabe de mí."

---

## 7. Limpieza (tras la demo)

```
DELETE _plugins/_security/api/rolesmapping/streaming_lector
DELETE _plugins/_security/api/internalusers/demo_lectura
DELETE _plugins/_security/api/roles/streaming_lector
DELETE _plugins/_security/api/roles/streaming_analista
DELETE _plugins/_security/api/tenants/analistas
```

---

## Resumen

```text
Usuario  → tiene backend_roles
Rol      → cluster + index (+ DLS/FLS) + tenant permissions
Mapping  → une usuarios/backend_roles ↔ roles  (sin esto, el rol no aplica)
Tenant   → aísla dashboards: Global / Private / propios por equipo
authinfo → para ver quién soy y qué puedo
```
