# Documentos de ejemplo para los dashboards:

```json
      "@timestamp":       { "type": "date" },
          FILTRO

      "event_id":         { "type": "keyword" },
      "event_type":       { "type": "keyword" },
      "service":          { "type": "keyword" },
      "environment":      { "type": "keyword" },
      "host":             { "type": "keyword" },
      "level":            { "type": "keyword" },
      "status_code":      { "type": "keyword" },
      "country":          { "type": "keyword" },
      "country_code":     { "type": "keyword" },
      "region":           { "type": "keyword" },
      "city":             { "type": "keyword" },
      "device_type":      { "type": "keyword" },
      "os":               { "type": "keyword" },
      "app_version":      { "type": "keyword" },
      "user_plan":        { "type": "keyword" },
      "isp":              { "type": "keyword" },
      "content_id":       { "type": "keyword" },
      "content_type":     { "type": "keyword" },
      "genre":            { "type": "keyword" },
      "error_code":       { "type": "keyword" },
      "cdn_provider":     { "type": "keyword" },
      "edge_node":        { "type": "keyword" },
      "request_method":   { "type": "keyword" },
      "api_endpoint":     { "type": "keyword" },
      "session_id":       { "type": "keyword" },
      "user_id":          { "type": "keyword" },

      "geo": {
        "properties": {
          "location":     { "type": "geo_point" }
        }
      },

      "latency_ms":       { "type": "integer" },
      "duration_ms":      { "type": "integer" },
      "bytes_sent":       { "type": "long" },
      "bitrate_kbps":     { "type": "integer" },
      "buffering_ms":     { "type": "integer" },
      "rebuffer_count":   { "type": "integer" },
      "cpu_client_pct":   { "type": "float" },
      "memory_client_mb": { "type": "integer" },

      "cache_hit":        { "type": "boolean" },
      "is_error":         { "type": "boolean" },
      "is_premium":       { "type": "boolean" },

      "content_title": {
        "type": "text",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "message":          { "type": "text" },
      "user_agent":       { "type": "text" }
    }
```

Es una empresa que hace streaming de video y tiene un NOC (Network Operations Center) que monitoriza la plataforma. Los dashboards están diseñados para dar visibilidad sobre el estado del sistema, errores, latencias, tráfico por dispositivo, etc.

Los documentos no son PELICULAS, NI USUARIOS. Lo que son:

Eventos:
- Un usuario comienza desde su dispositivo un streaming de video.
- Un segmento de viseo que se está reproduciendo en el dispositivo del usuario.
- Un login de un usuario en la plataforma que ha fallado
- Eventos de heartbeat de los servidores del NOC.

TIEMPO          @timestamp     Momento del evento (fecha y hora exacta).
TIPO DE EVENTO  event_type     Qué tipo de evento es:
                                    - playback_start
                                    - playback_stop
                                    - login
                                    - heartbeat
SERVICIO        service        Qué servicio generó el evento:
                host           host           El servidor donde se generó el evento.. y donde corre el servicio.
                environment    environment    El entorno donde se generó el evento (prod, staging, dev)
                edge_node      edge_node      Nodo de borde que sirvió el contenido
                request_method request_method Método HTTP usado en la petición (GET, POST)
                api_endpoint   api_endpoint   Endpoint de la API que se llamó


SEVERIDAD        level          Qué nivel de severidad tiene el evento (INFO, WARN, ERROR)
                 status_code     status_code    Qué código de estado HTTP se devolvió (200, 404, 500, 503, 504)
                 is_error        is_error       Booleano: si el evento es un error o no.
                 error_code      error_code     Código de error específico (CDN_TIMEOUT, RECOMMENDATION_API, etc.)

METRICAS         latency_ms     Latencia de la petición (en milisegundos)
                 buffering_ms   Tiempo de buffering (en milisegundos)
                 rebuffer_count Número de veces que se rebufferizó el video
                 bytes_sent     Cantidad de bytes enviados al cliente
                 bitrate_kbps   Bitrate del video en kbps
                 cpu_client_pct Porcentaje de CPU usado por el cliente
                 memory_client_mb Memoria usada por el cliente en MB
                 duration_ms    Duración del evento en milisegundos 
                 cache_hit      cache_hit      Booleano: si el evento fue cacheado o no.

GEOPOSICIALES    geo.location   Coordenadas geográficas del evento (latitud, longitud)
                 country        country        País del usuario
                 country_code   country_code   Código de país del usuario
                 region         region         Región del país del usuario
                 city           city           Ciudad del usuario

DISPOSITIVO_CLIENTE
                  device_type    device_type    Tipo de dispositivo del usuario (mobile, desktop, tablet)
                  os             os             Sistema operativo del dispositivo del usuario
                  app_version    app_version    Versión de la aplicación del cliente
                  user_plan      user_plan      Plan de suscripción del usuario (free, premium)
                  isp            isp            Proveedor de servicios de internet del usuario
                  cdn_provider   cdn_provider   Proveedor de CDN que sirvió el contenido

CONTENIDO
                  content_id     content_id     ID del contenido que se está reproduciendo
                  content_type   content_type   Tipo de contenido (movie, series, live)
                  genre          genre          Género del contenido (action, comedy, drama)

Resumiendo:
- Fecha
- Tipo de evento
- Servicio y host
- Severidad y códigos de error
- Métricas de latencia, buffering, rebuffering, bytes enviados, bitrate....
- Geoposición del usuario
- Dispositivo y sistema operativo del usuario
- Contenido que se está reproduciendo

Vamos a querer montar unos dashboards que nos den visibilidad de todo esto, para poder monitorizar la plataforma y detectar problemas rápidamente.

Los mappings tienen unos tipos de datos:
- keyword
- numérico (integer, long, float)
- boolean
- date
- geo_point
- text

ESO SON TIPOS DE DATOS DESDE EL PUNTO DE VISTA INFORMATICO.

Esos tipos de datos... VALEN MIERDA! Cuando lo que quiero es hacer unos dashboards.
Al hacer dashboards lo que necesito es tener en cuenta los tipos de datos desde el punto de vista ESTADISTICO... y esos no salen en Opensearch.
Esto es crítico... en base al tipo de dato ESTADTISTICO voy a poder hacer unas visualizaciones u otras.
El problema es que Opensearch no me restringe a hacer visualizaciones que no tienen sentido estadístico, y eso es un problema.
Y por eso es necesario comenzar identificando los tipos de datos estadísticos que hay en los documentos, y a partir de ahí diseñar los dashboards.

TIPOS DE DATOS ESTADISTICOS?
- CUALITATIVOS
  - NOMINALES
  - ORDINALES
- CUANTITATIVOS
  - DISCRETOS             - DE RAZON (Absolutos)
  - CONTINUOS             - DE INTERVALO

Código HTTP STATUS: 200
  entero      Me permite buscar por rangos:    2?? 3?? 4?? 5??
              Cuánto ocupa un int? 4 bytes

                1 byte puedo reopresentar cuantos valores diferentes? 256
                2 bytes puedo reopresentar cuantos valores diferentes? 65536
                3 bytes puedo reopresentar cuantos valores diferentes? 16.777.216
                4 bytes puedo reopresentar cuantos valores diferentes? 4.294.967.296                    int
                8 bytes puedo reopresentar cuantos valores diferentes? 18.446.744.073.709.551.616       long

  keyword     Orden alfabético podemos medio apañarnos.
              >= 200   <=299
              3 caracteres en HDD?3 bytes (ASCII, UTF-8) 1 byte por caracter

Puedo hacer una media de los códigos HTTP? NO
                suma

Quiero decir.. matemáticamente/ computacionalmente SI PUEDO. 
Tiene sentido esa operación? NINGUNA

Puedo hacer la media de CODIGOS POSTALES? NO

Puedo sumar números de portal en la calle? NO

  Vivo en el número 17 y tu en 23... Entre los en el 40
  De media vivimos en el portal 20... NO TIENE SENTIDO


CODIGO POSTAL -> NOMINAL
  unidad de medida? EIN???
CODIGO HTTP -> NOMINAL
  unidad de medida? EIN???
Número de la calle? -> ORDINAL
  unidad de medida? EIN???

Número de bytes mandados? CUANTITATIVO
  unidad de medida? Bytes
Número de hijos que tiene una familia?
  unidad de medida? hijos


TIPOS DE DATOS ESTADISTICOS?
- CUALITATIVOS
  - NOMINALES       nombres, sin relación entre si.
                    Qué puedo hacer con esos nombres? CLASIFICAR = GRUPOS

      iOS|Android|Windows|Linux|MacOS
      200,500,300

  - ORDINALES       también son nombres, pero hay una relación de intensidad entre ellos.
      bajo < medio < alto
                    Qué puedo hacer con datos ORDINALES? CLASIFICAR = GRUPOS
                                                         ORDENAR
- CUANTITATIVOS                                       (UNIDAD DE MEDIDA)
                    también son nombres, con una relación de intensidad entre ellos, y además tienen una unidad de medida.
                    Qué puedo hacer con datos ORDINALES? CLASIFICAR = GRUPOS
                                                         ORDENAR
                                                         OPERACIONES MATEMÁTICAS.. TODAS? +-*/
  - DISCRETOS             - DE RAZON (Absolutos).  +-*/     CUANDO HAY UN CERO ABSOLUTO
  - CONTINUOS             - DE INTERVALO           +-       CUANDO NO HAY CERO ABSOLUTO

  Número de hijos: CUANTITATIVOS (ud medida: hijo) DE RAON (0 hijos es un límite absoluto)
      Una familia tiene 2 hijos
      Otra familia tiene 4 hijos.
            Tiene sentido decir que la familia B tiene 2 hijos menos que la familia A? SI           4-2=2
            Tiene sentido decir que la familia B tiene el doble de hijos que la familia A? SI 4/2 = 2(doble)
  Temperatura en ºC en Sanlucar
    Día 1: 20º
    Día 2  -10º
          Tiene dsentido decir que el día 2 hizo 10 grados menos que el día 1? SI     20-10=10
          Tiene sentido decir que el día 1 hizo la mitad de temperatura que el día 2? NO 20/-10=-2 (no tiene sentido)

  Fechas!
    CUANTITATIVO DE INTERVALO
        15-06-2026
        17-06-2026
        Los resto y da: 2 días
        Hay un 0 absoluto? NO... 


Qué es la estadística? Ciencia que estudia CONJUNTOS DE DATOS.
Me da técnicas para lo primero: ENTENDER LOS DATOS QUE TENGO DELANTE.

    TENER LOS DATOS != ENTENDER LOS DATOS

    Nóminas de 5000 empleados.

Necesito RESUMIR LOS DATOS. Y eso es lo que hace la estadística, darme herramientas para resumir los datos, y poder entenderlos mejor.
- Herramienta más básica que me da la estadística para resumir datos: TABLA DE FRECUENCIAS
    Frecuencia? Cuantas veces ocurre / se repite algo.
    Qué necesito para poder crear una tabla de frecuencias? CLASIFICAR LOS DATOS EN GRUPOS

              CUANTOS ABSOLUTOS?        %
      altos     3                       20%
      Bajos     5                       33%
      Medios    7                       47%

  Por ende, a un dato CUALITATIVO NOMINAL puedo hacerle una tabla de frecuencias? SI
  Y a un dato CUALITATIVO ORDINAL puedo hacerle una tabla de frecuencias? SI
  Y a un dato CUANTITATIVO ? TAMBIEN ... PERO....
      Si es CONTINUO (con decimales)... cuanto grupos hay potencialmente? INFINITOS Entonces resumo algo? NADA NO APORTA
      Si es DISCRETO (sin decimales)... cuanto grupos hay potencialmente? FINITOS Entonces resumo algo? SI APORTA

    Esa tabla la puedo representar de forma gráfica: BARRAS o TARTA

    CUANTITATIVA -> ORDINAL
    1787.17           poco    0-1000            0     TABLA
    2349.87           medio   1000-2000        10     BARRAS
    2439.21           mucho   2000-3000        20     TARTA
                              3000-4000        30
                              4000-5000       500

              De media en Tedial cobran 4300€/mes
              De mediana en Tedial cobran 4000€/mes 

- Siguiente nivel de resumen... RESUMIR A UN NUMERO: ESTADISTICOS

  - Tendencia central: Me informa de POR DONDE VAN LOS TIROS!
    - MODA      Valor que más se repite <- TABLA DE FRECUENCIAS: NOMINALES , ORDINALES, CUANTITTIVOS
    - MEDIANA   Valor que divide en 2 a la población ORDENADA.
                   Que necesito para calcular una mediana? ORDENA LOS DATOS!!!! NOMINAL: NO PUEDO ORDENARLOS
                                                                                ORDINAL: SI PUEDO ORDENARLOS
                                                                                CUANTITATIVO: SI PUEDO ORDENARLOS
    - MEDIA     Atiende a una formula matematica     Suma todo / Numero de datos.
                Cuanto aporta cada dato al total si todos los datos aportasen lo mismo.
                      NOMINAL: NO.. no puedo sumarlos
                      ORDINAL: NO.. no puedo sumarlos
                      CUANTITATIVO: SI.. puedo sumarlos

  NOTA: Estas medidas han hecho mucho resumen sobre los datos... 100000 -> 1 número
  Pierdo mucha información por el camino.
  Y a veces sin querer ME/TE ENGAÑO cuando calculo este dato y te lo pongo en un dashboard.

  - Dispersión: JAMAS PUEDO DAR UNA MEDIDA DE TENDENCIA CENTRAL SIN SU DATO DE DISPERSION ASOCIADO
          Cuanto cambia la cos con respecto al POR DONDE VAN LOS TIROS! (TENDENCIA CENTRAL) 

            MEDIA -> Desviación típica

                Salario medio  = 4300€/mes con una desviación típica de 300€/mes
                  La mayoría de la gente gana entre 4000 y 4600? Al menos el 50%
                    Regla de Chevichev

            MEDIANA -> Rango semiintercuartílico = Q3-Q1 = P75-P25 /2

    Percentiles? El valor de la variable que deja por debajo un % de la población.

      P20 = 1200€ -> 20% de la población gana menos de 1200€
      P95 = 5000€ -> 95% de la población gana menos de 5000€
      P50 = 4000€ -> 50% de la población gana menos de 4000€ = MEDIANA = Q2 = segundo quartil = P50 = Mediana
      Q1 = P25%
      Q3 = P75%

      Cuánta gente hay entre el percentil 25 y el percentil 75? 50% de la población

---

Siempre empezamos con análisis UNIVARIABLES. Cojo una varaible y la analizo.
Cuando he hecho eso, paso a hacer análisis BIVARIABLES. Cojo 2 variables y las analizo juntas.
Y nos planteamos el juntar 3 variables en los dashboards? NO. El cerebro humano no da -> MACHINE LEARNING. Pero eso es otra historia.

OJO... otra cosa es sobre que conjunto de datos hago el estudio...
Y podré tener un conjunto de datos muy grande, que FILTRO por 500 variables.. -> CONJUNTO MAS CHIQUITO <- 2 variables como mucho para analizar.

---

Villarrriba de arriba: 10 vecinos

  5gCO/dia
  5
  5

  10
  10
  10
  10
  
  15
  15
  15

  Media: 10gCo/dia
  Mediana: 10gCO/dia

---

Villarrriba de abajo: 10 vecinos

  5
  5
  5
  5
  5
  5
  5
  5
  5
  1000g/CO/dia

  Media: 45+1000 = 1045/10 = 104.5gCO/dia
  Mediana: 5gCO/dia


----

Histograma

Sobre tipo de datos podemos generar un histograma?
Un histograma es = a un grafico de barras, con una diferencia

  Frecuencia (Count)
  ^
  |
  |
  |
  |
  |
  |
  +---------------------------------------------- X
            Valores de la variable

    Login   Logout   Start video play           A priori no hay criteo de ordenación: LA VARIABLE ES NOMINAL
          Variable Tipo de evento


    200 201 202 203 400 401 402 403 500        A priori no hay criterio de ordenación: LA VARIABLE ES NOMINAL. ORDEN ALFABETICO
          Variable Código HTTP

    Quizás los muestro por orden de FRECUENCIA (MUY HABITUAL)

    200 201 400 403 301

    Ventas por ciudad

    SUMA(en lugar de frecuencia)

    Malaga   Gijon  Madrid   Barcelona Ordeno por orden de venta

    Las barras están pensandas para datos CUALITATIVOS

Cuando tengo un dato CUANTITATIVO: EL EQUIVALENTE AL GRAFICO DE BARRAS ES EL HISTOGRAMA

  Frecuencia (Count)
  ^
  |
  |
  |
  |
  |
  |
  +---------------------------------------------> X
    1 2 3 4 5 6 7 8 9 10 11 
            Valores de la variable van ordenados por la propia variable (de menor a mayor)

Las fechas como son datos CUANTITATIVOS, los represento mediante un histograma, y no mediante un grafico de barras.
Pero cualquier variable cuantitativa la pinto como histograma

Queremos saber cuanto tráfico movemos         BYTES
               ESTADISTICO                    SUMA
Pero la quiero calculada para cada hora