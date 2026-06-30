# PPL

Lenguaje de consulta por PIPES (Tuberias) para OpenSearch. Son como pipes de Linux, donde cada comando recibe la salida del anterior y la transforma. Se usa mucho en la parte de Observability (Logs y Event Analytics) y en Query Workbench.

query -> COMANDO1 | COMANDO2 | COMANDO3 ...

 Cada | toma el resultado del paso anterior y le aplica el siguiente comando.
Estas queries las podeis usar también desde API REST, en Dev Tools, con:

```
POST _plugins/_ppl
{ "query": "..." }
```

# El comienzo

Siempre empezamos por la fuente de datos, que es un índice de OpenSearch. Por ejemplo:

 source = INDICE (alias)

# Otros comandos que tenemos:

## `where` → filtra los resultados (como el WHERE de SQL)

    source = logs-apache | where status-code = 404

## `fields` → elige qué columnas quieres ver

    source = logs-apache | where status-code = 404 | fields timestamp, url, status-code

## `sort` → ordena los resultados

    source = logs-apache | where status-code = 404 | fields timestamp, url, status-code | sort - timestamp

    Si pongo un + delante de la columna, ordena ascendente. Si pongo un -, ordena descendente.

## `stats` → estadísticas de una columna (en SQL el equivalente sería un GROUP BY + Operaciones de agregación: SUM, COUNT...)

    source = logs-apache | stats <metrica> as <nombre-columna> by <campo-agrupación>

    Esto nos devuelve un resumen de cuántos logs hay de cada código de estado.

    Méticas:
        - count() → cuenta el número de documentos
        - sum(<campo>) → suma los valores de un campo numérico
        - avg(<campo>) → media de los valores de un campo numérico
        - min(<campo>) → mínimo de los valores de un campo numérico
        - max(<campo>) → máximo de los valores de un campo numérico
        - percentile(<campo>, <percentil>) → percentil de los valores de un campo numérico
        - dc(<campo>) → cuenta el número de valores distintos de un campo

    source = logs-apache | stats avg(latency) as latencia-media by country-code:

        CC                  latencia-media
        ----------------------------------
        ES                  0.123
        US                  0.456                   La puedo querer ver como tabla o como una visualización.

    
    Puedo sacar varias métricas:

    source = logs-apache | stats count() as total, avg(latency) as latencia-media by country-code:

## `head` → limita el número de resultados (como LIMIT de SQL)

    source = logs-apache | head 5

## `eval` → crea nuevas columnas a partir de expresiones

    source = logs-apache | eval lento = latency > 1000 | stats count() as total by lento

## `top` ~ `rare` Mayor o menor frecuencia de un campo. Devuelve el valor y el número de veces que aparece.

    source = logs-apache | top 5 url 

    source = logs-apache | rare 5 url

## `dedup` → elimina duplicados de un campo

    source = logs-apache | fields url | dedup url  ->   Listado de las urls únicas.

## `rename` → renombra una columna

    source = logs-apache | rename latency as latencia


---

# Operativa a la hora de trabajar con logs.

Tenemos "discover" / "dashboard" dentro de Openseach DASHBOARDS.

Pero para logs hay otras 2 herramientas: "logs" y "dashboards" (dentro de observability).

La primera:
- Sirve para ver logs en tiempo real
- También sirve para crear queries que voy a guardar como tablas de datos o como visualizaciones para usar en dashboards (DE OBSERVABILITY).

La segunda:
- Sirve para crear dashboards de visualizaciones de logs y métricas (DE OBSERVABILITY).

# Son distintos los dashboards de "Observability" y los de "Dashboards" (de OpenSearch Dashboards).

SI. Son muy distintos. Cuál es mejor? No hay uno mejor que otro. Son diferentes.
Y lo cierto es que aunque estén separados en "Dashboards" y "Observability", en realidad son complementarios y en muchos caso me puede incluso interesar usar "DASHBOPARDS TRADICIONALES" para trabajar con logs e incluso DASHBOARDS DE OBSERVABILITY para trabajar con métricas.

No hay una regla que diga que para cada cosa debo usar uno u otro tipo de dashboard. Depende de lo que quiera hacer y de cómo me sienta más cómodo.

DIFERENCIAS NOTABLES ENTRE ELLOS:
- Dashboards tradicionales: 
  - Tiene más (MUCHAS MAS) visualizaciones que los de observability.
  - El lenguaje es DQL 
- Dashboards de observability:
  - Tiene menos visualizaciones que los de dashboards tradicionales.
  - El lenguaje es PPL

Es mejor un lenguaje que otro? 
Son distintos.
Pero si tienen una gran diferencia.
- PPL comienza con la fuente de datos (índice) y luego le aplico los comandos.
- DQL NO INCLUYE la fuente de datos (índice)... solo filtros, queries y agregaciones. La fuente de datos se elige en la parte de "Data source" del panel de visualización.

Con Los dashboards tradicionales, los filtros, queries aplcian a todas las visualizaciones del dashboard. 

Con los dashboards de observability, cada visualización se construye con su propio PPL (query) y tiene sus propios filtros y queries.

Puedo mezclar visualizaciones que trabajen contra distitnos conjuntos de datos (indices) filtrados de distinta forma dentro de un mismo dashboard de observability. Y esto me puede interesar. Si es el caso, posiblemente me interesa trabajar con dashboards de observability.

Si por contra, quiero que todas las visualizaciones de un dashboard trabajen contra el mismo conjunto de datos (índice) filtrado de la misma forma, posiblemente me interesa trabajar con dashboards tradicionales.


---

logs-apache         logs
logs-keycloak
logs-postgres

Tienen muchos campos comunes.
Pero luego tienen sus campos específicos.

Objetivo: Montar un dashboard de observability que tenga visualizaciones de logs de distintos indices , pero algunas de ellas teniendo en cuenta TODOS LOS INDICES.. y campos comunes.
Por otro lado, otras visualizaciones que tengan en cuenta solo un índice y sus campos específicos.

---


DASHBOARD
    - Histopgrama de eventos por tiempo (por todos los indices) y tipo de servicio      <-- Aqui no aplico el filtro
    - Histograma de errores por tiempo (por todos los indices) y tipo de servicio       <--- Aplico un filtro de tipo de evento = error o fatal
    - HeatMap cantidad y tiempos medios de servicio por tipo de evento                  <-- Aquí tampoco aplico el filtro
Esos de ahi son todos aparentemente iguales... 
    - Número de solicitudes de mensaje en Rabbit...     <--- Esto es otro indice... con otra estructura MAL ASUNTO EN DASHBOARDS TRADICIONAL.


---

OBSERVABILITY VA PENSADO PARA TENER UN DASHBOARD QUE PROYECTO EN UN MONITOR... en tiempo real.. para OBSERVABILITY!

DASHBOARDS A PRIORI NO ESTÁ PENSADO PARA ESO... aunque puedo usarlo.

Si quiero proyectar en un monitor, tengo un monitor = UN DASHBOARD... o 3 monitores = 3 DASHBOARDS...
Y quiero sacar en ellos información MUY VARIOPINTA (distintos filtros, indices... todo mezclado) y que se actualice en tiempo real. Entonces me interesa usar dashboards de observability.

Si tengo esa variedad... si no puedo crear un alias comun... Si quiero datos muy especificos (con filtros propios) en cada visualización me creo un dashboard de observability.

Pero son mucho mucho menos potentes.

- Si tengo logs...
  - TOMCAT escribe ERROR | FATAL
  - Microservicio... EXCEPTION


---


Quiero mirar si un servicio da un 500 HTTP.
Quiero mirar tiempos de respuesta de un servicio.
Quiero mirar consumo de RAM y CPU de un servicio.
TAMAÑO DE COLA EN rabbit
tamaño de cola de pool de ejecutores en tomcat
Memoria de la JVM del tomcat
Memoria de la JVM del opensearch
Quiero mirar Espacio libre de almacenamiento.
Quiero mirar si todos los nodos están operativos del ES.. y del rabbit

    GRAFANA

    ELASTIC <- LOGS

    LOG DA PISTAS DE QUE ESTA PASANDO y de COMO SE COMPORTA EL SISTEMA.

        CODIGOS HTTP y los tiempos se controlan a otro nivel (COMUNICACIONES)
