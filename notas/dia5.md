
# Dashboards

- Conceptos de estadística
    Tipos de variables: 
        Cualitativas 
            Nominales
            Ordinales
        Cuantitativas (Ud de medida)

- Siempre puedo sacar tablas de frecuencia. 
  En el caso de variables cuantitativas continuas (con decimales) agrupamos primero -> Convertimos la variable en ORDINAL.

- Esas tablas las podemos representar con gráficos de barras, sectores (%), histogramas, etc.
- Resumiendo más ->
  - Estadístico de tendencia central: Media, Mediana, Moda
  - Estadístico de dispersión: Rango, Varianza, Desviación típica,
            - Media -> Desviación típica
            - Mediana -> Rango intercuartílico (Q3-Q1)
- En ocasiones, en tablas no spueden interesar: 
  - Suma/Total
  - Percentiles (JUGAMOS MUCHO CON ELLOS)
  - Máximo y mínimo.. no tanto. P95(P99), P1 (P5) son más interesantes.

A la hora de generar dashboard:
- Siempre:
  - De lo más general a los más concreto

        Cuadro de mando GENERAL... Sin mezclar variables (estudios univariables)
            - Cuantos eventos   <- Count (FRECUENCIA)
            - Cuantos errores   <- Cuantos eventos de cada tipo (pie, barras, tabla)
            - Cuanta latencia   <- Mediana P95
            - Cuantos bytes     <- SUMA

            Una vez hecho eso, hay variables que si las tenemos, nos gusta intruducirlas en los gráficos adicionalmente... incluso en el principal.
                INFORMACION DE GEOPOSICIONAMIENTO (MAPA)


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


    Elegimos una variable de trabajo: 
        - Cantidad de eventos
        - Cantidad de errores
        - Suma de tráfico
        - Media (o percentil o mediana) de latencia

    El filtro de tiempo siempre está activo. (Potencialmente otros filtros que se vayan aplicando)

    Y lo que represento es el valor de esa variable en función de la variable de geoposicionamiento (ciudad, región, país, cc, lat/lon).

    Para representarlo, usamos un MAPA.
    Hay mapas especiales para pintar lat/long. En este caso, se juntan puntos (documentos) con lat/log muy parecidas... para calcular el agregado.
    Pero hay mapas en los que representamos fronteras GEOPOLITICAS: PAISES, REGIONES (Comunidades autonómicas, provincias, etc), CIUDADES (municipios).
    
    En estos casos, el mapa no lleva solo la imagen del mundo/pais + delimitaciones geopolíticas, sino que lleva información de la ciudad/región, pai asociado a cada delimitación. ES UN NOMBRE que viene embebido en el mapa. Y ese nombre es el que usamos para hacer el JOIN con la variable de geoposicionamiento que tenemos en los documentos.

    Es importante que use un mapa que contenta los mismos términos que yo tengo en mis documentos... SI NO NO HAY FORMA DE HACER MATCH


        Errores

                5 10 15 20
        
        INVERSA = (MAX (Errores) - Errores) = 20 -X
                15 10 5 0

---

En la Visualización "Maps" podemos represetar no solo datos agregados, sino también DOCUMENTOS SUELTOS.
  - Monto Wallapop
    - Búsqueda de coches que se venden de un determinado tipo... y quiero que cada coche se pinte en su ubicación. (Cada documento es un coche, y cada coche tiene lat/lon)
  - Monto Booking
    - Búsqueda de hoteles en una ciudad... y quiero que cada hotel se pinte en su ubicación. (Cada documento es un hotel, y cada hotel tiene lat/lon)
  - Monto radar flight
    - Búsqueda de estado de vuelos.
      - Trabajo con 2 índices:
        - 1. Vuelos planificados con Origen y destino (cada documento es un vuelo, y cada vuelo tiene lat/lon de origen y destino)
              Y pido que se represente ese documento como una linea! 
        - 2. 1 campo de goposicion: UBICACION ACTUAL (que manda el gps cada 5 minutos) Cada 5 mins se hace un update del documento del vuelo con la nueva ubicación. Y quiero que se represente ese documento como un punto (lat/lon) que se mueve en el mapa.
  - Una empresa de taxis o transporte, para ver donde está cada cual.
  - UberEats.

---


Esos son los mapas de verdad MAPAS:
    - Coordinate map (lat/long)
    - Region map (Shapes: Región, País)
    - Map        (Admiten multiples capas) Cada capa puede ser: Un mapa(dibujo) | heatmap(similares a los coordinate maps) | documentos sueltos (lat/lon)

---

Pero en dashboards encontramos otra visualización que pone mapa... y no tiene nada que ver con MAPAS.
HEAT MAP.
Eso es la representación de lo que en estadística se llama una tabla de contingencia. 
Es una tabla de frecuencias de doble entrada, donde en cada celda hay un valor (suma, media, percentil, etc) en base a 2 variables.
Lo que pasa es que en lugar de ver la tabla, vemos colores...en base a la magnitud del valor de cada celda.

Las variables que se represnetan en este tipo de gráficos deben ser NOMINALES | ORDINALES. CUALITATIVAS.
- Servicio
- Códigos de respuesta HTTP
- Nivel de evento (Info, Warning, Error)
- Pais
- ...


                    INFO    WARNING   ERROR
    SERVICIO 1      17          44      44
    SERVICIO 2      0           77      12
    SERVICIO 3



---

<iframe src="https://dashboards.iochannel.tech/app/dashboards#/view/f8a174e0-73bd-11f1-a3c9-5f488008b209?embed=true&_g=(filters:!(),query:(language:kuery,query:''),refreshInterval:(pause:!t,value:0),time:(from:now-3w,to:now))&_a=(description:'',filters:!(),fullScreenMode:!f,options:(hidePanelTitles:!f,useMargins:!t),query:(language:kuery,query:''),timeRestore:!t,title:'Dashboard%20avanzado%20Iv%C3%A1n',viewMode:view)" height="600" width="800"></iframe>


https://dashboards.iochannel.tech/goto/8d69d558cf6b96db7e4b4480b2eb432b

---

# Procedimiento de Ingesta

## Cluster de contenidos

La ingesta es poca y mediante un software propio que habéis desarrollado.

## Cluster de logs

La ingesta es alta. Y usamos herramientas estandar.

En vuestro caso, teneís una variedad de servicios de backend/infraestructura importante:
- BBDD (postgres...)
- Sistemas de mensajería (Rabbit)
- Sistema de autenticación (Keycloak)
- Vuestros servicios/aplicaciones

Esas herramientas van escribiendo a ficheros de log.
No es válido que los logs se persistan en las mismas máquinas (contenedores dentro de un cluster de Kubernetes/OKD) donde se van generando.

# Seguridad / acceso a los datos

Keycloak


---

# Contenedorización

Es una forma alternativa de desplegar/instalar software en entornos de producción (también se usa en entornos de desarrollo).

## Instalación tradicional

           App1 + App2 + App3               Para un equipo de un usuario esto vale.
    --------------------------------        Para un entorno de producción NO.
           Sistema Operativo                    Problemas graves:
    --------------------------------                    Seguridad, Incompatibilidad.
            Equipo / HIERRO                             App1 pone la CPU 100% (BUG) ---> App1 OFFLINE
                                                                                         App2 y App3 van detras!

## Instalación basada en máquinas virtuales

        App1  |     App2 + App3
    ---------------------------------       Esto, nos resuelve los problemas de las instalaciones tradicionales. Por crear entornos aislados donde ejecutar cada aplicación. 
        SO1   |          SO2                Esto sale caro! Muy caro. Necesito montar varios SO... que hay que mantener actualizados. Configurar.
    ---------------------------------
        MV1   |          MV2     
    ---------------------------------          Además, tengo una merma de recursos.
        Hipervisor: VMware,                    Las apps vcan más lentas. Merma en el rendimiento
        VirtualBox, HyperV
    ---------------------------------
        Sistema operativo
    ---------------------------------
            Equipo / HIERRO

## Instalaciones basadas en contenedores

        App1  |     App2 + App3
    ---------------------------------       Esto es otra forma de resolver los problemas de las instalaciones tradicionales.
        C1    |          C2                 Por crear entornos aislados donde ejecutar cada aplicación. Pero es más eficiente y barato que las máquinas virtuales.
    ---------------------------------
        Gestor de contenedores                  En un contenedor no es posible montar un Sistema Operativo, como si pasa con las VMs.
        Docker, Porman, ContainerD              Y esa es la gran diferencia. 
    ---------------------------------
        Sistema operativo Linux                 No resuelven todos los problemas que resuelven las VMs... pero muchos si.
    ---------------------------------
            Equipo / HIERRO

## Vuestra instalación:


        App1   |     App2 + App3
    ---------------------------------       
        C1     |          C2                
    ---------------------------------
        Docker |        Docker
    ---------------------------------
        SO1   |          SO2         
    ---------------------------------
        MV1   |          MV2     
    ---------------------------------
        Hipervisor: VMware
    ---------------------------------
        Sistema operativo
    ---------------------------------
            Equipo / HIERRO

La instalación usa tanto máquinas virtuales como contenedores.

Pero lo hace de forma eficiente.
Antiguamente habriamos creado 1 VM por cada aplicación (BBDD en una VM, Rabbit en otra, Keycloak en otra, cada servicio en otra). Eso es muy caro y poco eficiente.
Ahora creo Máquinas virtuales (pocas) que dentro ejecutan cada una muchas aplicaciones, dentro cada una de ellas en un contenedor. Eso es mucho más eficiente y barato.

Y a la vez más sencilla de gestionar.

El tema importante es que en un entorno de Producción tenemos que ofrecer Alta disponibilidad y escalabilidad. En vuestro caso, sobre todo, vuestra instalación va orientada a la HA (High Availability: Alta disponibilidad). Es decir, a poder seguir ofreciendo sevricio aunque un hardware (o software) falle.

Para ello, necesitamos tener HARDWARE y SOFTWARE REDUNDANTE. 
Tengo 3 máquinas y de ellas, los recursos nunca pasan del 50-60%. Eso me permite que si una máquina falla, las otras 2 puedan asumir la carga de trabajo de la que ha fallado. Y eso es lo que hace vuestra instalación.
Tengop normalmente (y ojalá por siempre) las máquinas infrautilizadas.... Podría estar trabajando habitualmente con máquinas mucho más básicas y BARATAS. 
Pero si una se jode... no tendría otra suficientemente potente para asumir la carga de trabajo de la que ha fallado. 
Habitualmente estamos desperdiciando máquina. Y ESO DEBE SER ASI. La HA es cara.

En vuestro caso, teneís montada una utilidad llamada OKD. Eso es una distribución de una herramienta llamada KUBERNETES!
Kubernetes tiene muchas distribuciones (kubernetes + plugins que le ponen encima para ampliar la funcionalidad estanda)
- Redhat hace uno
- VMWare hace otra distribución de kubernetes
- Hay muchas.

En vuestro caso usaís una llamada OKD. Es Opensource y gratuita. Y está respaldada por REDHAT. De hecho es la que nutre a la distribución de Redhat OPENSHIFT.

Kubernetes (y sus distribuciones) nos ayudan a definir y operar en automático (sin intervención humana) un entorno de producción (de varias máquinas) donde desplegar aplicaciones (contenedores) de forma eficiente, segura y tolerante a fallos.

Ofrece funcionalidades de forma que si un programa deja de funcionar en una máquina o incluso si una máquina se rompe, el sistema(kubernetes) lo detecta y automáticamente levanta ese programa en otra máquina, o al menos se asegura que exista previamente otra copia de ese programa que pueda seguir ofreciendo servicio al usuario final.


Todas las herramienats de software empresarial hoy en día se recomienda instalarlas mediante esta técnica (contenerización) y no mediante la instalación tradicional.
Y todos los fabricantes (ketycloak, Elastic, Opensearch, Postgres, Rabbit, etc) documenta y ofrecen los recursos necesarios para instalar sus productos de esta forma.


                            VM1     VM2     VM3 
                            MAQUINAS FISICA 1
                            
                            
                            VM1     VM2     VM3 
                            MAQUINAS FISICA2

Y dentro de cada VM pongo a funcionar un monton de programas... cada uno en su contenedor.

Y entonces kubernetes se encarga de ofrecer un primer nivel de alta disponibilidad y escalabilidad.

Vuestro ES esta trabajando en un cluster de 3 nodos. Cada nodo es un contenedor que se ejecuta en una máquina virtual. Y cada máquina virtual se ejecuta en un servidor físico.
Vuestro keycloak se ejecuta en un contenedor, que corre en una máquina virtual, que corre en un servidor físico. Y lo mismo para cada uno de los servicios que habéis desarrollado.

Sea como fuere, cada programa tiene su propio entorno de trabajo... (Y algo así como su propio HDD).
Tengo Tomcat como servidor de aplicaciones de nuestros microservicios.. y esos tomcats generan logs.. y mis aplicaciones (microservicios) generan logs. Y esos logs se escriben en ficheros de log que están dentro del contenedor donde se ejecuta cada programa.
El keycloak igual.. y así muchos.

Si uno de esos entornos... o incluso una máquina física se jode, perdería el acceso a los logs! Y POSIBLEMENTE AHI SEA CUANDO MAS ME INTERESA TENER LOS LOGS. Para poder investigar que ha pasado y por qué ha fallado el sistema.
Además, esos "entornos" donde ejecuto TOMCAT, KEYCLOAK, RABBIT, POSTGRES, etc... tiene limitaciones de espacio de almacenamiento. Y si no hago nada, esos ficheros de log se van a ir llenando y en algún momento se va a quedar sin espacio y el programa va a dejar de funcionar.

Necesitamos sacar los logs de esas máquinas... Porque además hay otra cosa.
Tengo 20 aplicaciones funcionando... Tengo que estar mirando 20 archivos diferentes en 20 máquinas a ver si pasa algo? NO ME DA LA VIDA.

Aquí entre Opensearch y Opensearch Dashboards nos ayudan a centralizar los logs y su visualización.


    KeyCloak + FluentD
           v  ^
        -> log 
    Tomcat1 + FluentD                                                          Cluster de Opensearch
        -> log                                                                      Nodo1
    Tomcat2 + FluentD      >>>>>>>   Rabbit/ Kafka   >>> DataPepper  >>>>>>         Nodo2
        -> log                    Esto es muy estable                               Nodo3
    Postgres + FluentD
        -> log
    Rabbit + FluentD
        -> log
    MiApp1 + FluentD
        -> log custom


        DataPepper (en el mundo ElasticSearch llamado Logstash) es un software que se encarga de recibir los logs habitualmente de un sistema de mensajería tipo kafka o rabbit, transformarlos y enviarlos a Opensearch con tranquilidad... sin estresar mucho el cluster.

        Y aunque FluentD puede hacer transformación de los logs, lo más habitual es que solo haga el envío a un sistema de mensajería (Kafka o Rabbit) y que sea DataPepper el que haga la transformación y el envío a Opensearch.

        Hacer la transformación lleva curro... (= GASTA CPU) y la cpu donde se ejecuta el Keycloak o el Tomcat la reervo para el keycloak o el tomcat... y no para hacer transformaciones de logs. Por eso se hace en otro sitio (DataPepper) que está preparado para ello.

        Rabbit o kafke me sirven para ir acumulando mensajes. Y ya el datapepper va sacando mensajes de ahí y enviándolos a Opensearch... a su ritmo.
        Hacen las veces de un EMBALSE donde ir acumulando mensajes y que no se me pierdan si el cluster de Opensearch está saturado o caído.

Cada linea que se escribe en un fichero de log, FlUENTD la toma de forma independiente y la envía a ES/Opensearch. (A veces empaquetamos varias... para optimizar el envío, pero lo habitual es que cada linea sea un mensaje independiente). Y cada mensaje es un documento independiente en Opensearch. Y cada documento tiene su propio ID único. Y cada documento tiene su propio timestamp (cuando se escribió en el log). Y cada documento tiene su propio contenido (el mensaje del log).

>               "] o.s.m.s.b.SimpleBrokerMessageHandler     : Stopped."      53 caracteres... Que son unos 53 bytes en DISCO

Opensearch solo come JSON... no textos.
FluentD transforma eso en JSON.. y lo "enriquece" "un poco". Qué significa esto.. que una cosa es lo que escribimos en el fichero de texto.. y otra lo que se manda al Opensearch.


```json
{
    "@timestamp": "2026-06-10T15:22:32.143Z",
    "logtime": "2026-06-10T15:22:32.142Z",
    "message": "] o.s.m.s.b.SimpleBrokerMessageHandler     : Stopped.",
    "logtag": "F",
    "time": "2026-06-10T15:22:32.142842261+00:00",
    "level": "INFO",
    "thread": "ionShutdownHook",
    "pid": "21",
    "stream": "stdout",
    "kubernetes": {
      "labels": {
        "ted-environment": "pro",
        "ted-release": "4.1.0",
        "app_version": "4.1.0-13",
        "ted-tenant": "qa-cicd",
        "ted-appname": "platform-ui",
        "app.kubernetes.io/part-of": "platform-ui",
        "ted-ecosystem": "platform",
        "pod-template-hash": "9b8596587"
      },
      "pod_id": "6bba8369-3289-4cfd-9e57-f26a949abbe6",
      "docker_id": "5c387253bef34359e416bcd087fcab0f9564dae6f00562f27ac192fdbdad09c6",
      "pod_ip": "10.131.0.246",
      "pod_name": "platform-ui-9b8596587-cfs4z",
      "host": "qa-cicd-bblkm-worker-4",
      "container_name": "platform-ui",
      "container_hash": "europe-southwest1-docker.pkg.dev/clouvip-static-resources/tedial/platform-ui@sha256:6892d7bad98a97bdf2f45d3f2baeb44cde0b83da993a9f419412306b56677813",
      "container_image": "europe-southwest1-docker.pkg.dev/clouvip-static-resources/tedial/platform-ui:4.1.0-13",
      "namespace_name": "qa-cicd-platform-pro"
    },
    "class": "[",
    "tedial_target_index": "log-qa-cicd-platform-pro-2026-23"
}
```

53 -> 1400 bytes...
Y luego... el Opensearch..,. hace varias COPIAS... y luego backups... Cada 53 bytes... se convierten en 3 copias 4000 bytes + backups... 6kb-7kb.

Una labor que se esta planteando es prefiltrar un poco estos ficheros.

"Enriquece".. mete información valiosa. Pero también mucha morralla. Que conviene filtrar. ESTAIS EN ELLO. ESTUDIANDOLO.

Una cosa es lo que se escribe en el log.. y otra lo que llega al Opensearch.. y SI QUE QUIERO MAS INFORMACION DE LA QUE HAY EN EL LOG. Por ejemplo: La máquina donde se ejecuta el contenedor, el contenedor donde se ejecuta el programa, qué programa ha sido el que ha escrito.

Esto es lo que en vuestro caso, FLUENT manda al cluster de Opensearch. Y lo que en otrosescenarios se guarda en un Sistema de mensajería y esprocesado por DataPepper y enviado a Opensearch.

Estamos hablando de cientos de mensajes por segundo.
En principio para Opensearch no es problema... Lo que si es problema es lo que pasa cuando tenemos datos acumulados de MESES Y MESES...
Hay aplicaciones que mandan GIGAS por semana.
Por eso hablábamos de INDICES independientes por unidad de tiempo (día, semana, mes...) y les aplicamos políticas de ciclo de vida .

Al mes / semana, se congela, se compacta (quitar fragmentación y reescribir los archivos de segmentos).
Al tiempo los borro.

Esos índices, SIEMPRE DEBEN LLEVAR UN CAMPO DE FECHA (@timestamp = NOIMBRE ESTANDAR EN UN CLUSTER DE OPENSEARCH).

Lo normal es que a los documentos (LINEAS DE LOS ARHCIVOS DE LOG) de estos índices, no accedamos por la herramienta DISCOVER!

Lo normal es acceder vía LOGS dentro de OBSERVABILITY.

Queremos todosloslogs de todaslasaplicacionesde nuestro entorno de producción. 
    1 SOLA PANTALLA PARA GOBERNARLOS A TODOS!

En la pantalla de logs no buscamos en un índice. NO TIENE SENTIDO:
    - 1. Tendré muchos programas... y posiblemente cada uno escriba en un índice diferente.
    - 2. El mismo programa irá escribiendo en índices diferentes a lo largo del tiempo (por ejemplo, un índice por semana). Y si quiero ver los logs de un programa de hace 3 semanas, tendré que buscar en 3 índices diferentes.

Necesito condigurar algo así como hacíamos en discover,usaremospatrones de índices... y tiramos también mucho de alias.


Lo más normal es:
1. ACCEDER por discovery
2. Realizar/Configurar una búsqueda (filtros, ordenación, columnas, etc)
3. Guardar esa búsqueda (SAVED SEARCH)
4. Usar esa búsqueda guardada en un DASHBOARD (como un widget más)

En paralelo, vamos a configurar un PPL (Piped Processing Language) para ir monitorizando en tiempo real los logs de nuestros servicios.


A nivel de dashboard para monitorizar los logs de nuestros servicios, lo más normal es:

- Numero de eventos <- HISTOGRAMA (FRECUENCIA) de cada minuto.
- Numero de errores (LEVEL: ERROR, WARNING, INFO)
- En el texto busque la palabra ERROR
- Sacar otras métricas de funcionamiento

DE HECHO, es lo que hemos estado haciendo estos días en DASHBOARDS.