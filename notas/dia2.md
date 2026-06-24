# Índice como concepto genérico

Copia ordenada de un conjunto de datos incluyendo la ubicación original del dato!

## Indides directos vs inversos.

Inversos sirven para hacer búsquedas fulltext.
El cualquier caso, sea directo o inverso... la gracia de tener un índice -> los datos preordenados es que porque podemos aplicar un algoritmo de búsqueda mucho más eficiente (búsqueda BINARIA)... que precisa lon(Nª de elementos) operaciones para encontrar un elemento en un conjunto de datos ordenado.

## Índices inversos...

Cómo se gesta un índice inverso?
Los datos pasan por un proceso bastante pesado, que incluye cosas como:
- Tokenización (separar palabras)
- Normalización (poner todo en minúsculas, quitar acentos, etc)
- Stemming (quitar sufijos, por ejemplo: "correr", "corriendo", "corrió" -> "corr")
- Stopwords (quitar palabras que no aportan valor a la búsqueda, como "el", "la", "de", etc)
- ...

Son los términos resultantes de este proceso los que se guardan en el índice inverso, y no los documentos originales (bueno.. de ellos una copia si guardamos).

# Opensearch

Dijimos que opensearch viene de ElasticSearch, que es un indexador/motor de búsqueda de Elastic Inc.
Pero que cambiaron la licencia a una licencia propietaria y por eso Amazon decidió crear un fork de ElasticSearch y llamarlo OpenSearch.

Pero Opensearch/Elasticsearch saben generar índices (directos o inversos)? NO
Quién lo hace? LUCENE (Proyecto de la Apache Software Foundation) que es una librería de Java que sabe generar índices y hacer búsquedas sobre ellos.

Y que leches pintan entonces Opensearch/Elasticsearch?
- Orquestadores de lucenes, con qué objetivo tener varios lucenes? ESCALABILIDAD + ALTA DISPONIBILIDAD
- Lucene habla JAVA, Opensearch/Elasticsearch hablan REST (HTTP + JSON) y por ende, puedo hablar con Elasticsearch/Opensearch desde cualquier lenguaje de programación que sepa hablar HTTP y JSON.
- Gestión de usuarios/Autenticación/Gestión de permisos/Seguridad
- Políticas de mantenimiento de índices (rotación, borrado, etc)
- ...

# En Opensearch, existe el concepto de INDICE

Pero parece que en Opensearch un INDICE no es lo que habiamos explicado nosotros inicialmente.
En Opensearch un índice es un conjunto de DOCUMENTOS, sobre los que puedo hacer búsquedas.
Esos documentos son almacenados (realmente índexados) por LUCENES... montonoes de Lucenes...
El índice es también una colección de LUCENES.

Ahora bien... esos lucenes (en Opensearch llamados: SHARDS o FRAGMENTOS) no todos son iguales entre si. Había de 2 tipos:
- Primarios... Los documentos que se guardan en un shard primario, no están en ningún otro shard primario. Es decir, un documento está en un shard primario y solo en ese shard primario.
- Réplicas...  De los shards primarios tenemos réplicas, que contienen exactamente los mismos documentos que el shard primario, pero en otro nodo del cluster. Esto es para garantizar la alta disponibilidad de los datos.

Cuándo subiríamos primarios? Más capacidad de ingesta
Cúando subiríamos réplicas? Más capacidad de lectura y más alta disponibilidad.

# Para que leches usamos ElasticSearch?

- Indexar contenidos y hacer búsquedas COMPLEJAS sobre ellos muy eficiente
- Recopilar/aglutinar logs desistemas/aplicaciones...para tener un punto único de consulta y de análisis

---

# Opensearch Dashboards es OTRA COSA

Es una herramienta WEB que me permite conectar con un cluster de OPENSEARCH/ELASTICSEARCH para:
- Hacer búsquedas sobre los datos
- Visualizar los datos de forma gráfica (gráficas, tablas, mapas, etc)
- Crear dashboards (paneles de control) con las visualizaciones que yo quiera.
- Monitorizar logs
- Gestionar algunas operaciones de mantenimiento de los índices que hay en el cluster de Opensearch/Elasticsearch.
- Lanzar peticiones HTTP al OpenSearch/ElasticSearch (como si fuera un cliente REST)
- ...

    Cluster de ES/OS            <-- PETICION HTTP ---
      Nodo1 de Opensearch   \
      Nodo2 de Opensearch   -+- Balanceador de carga <- Clientes:
      Nodo3 de Opensearch   /                               - Opensearch Dashboards
                                                            - FluentD
                                                            - Gelastic (JAVA)
                                                            - Navegador
                                                            - CURL

---

Estados de un cluster de ES/OS:
- GREEN    = COJONUDO!
- YELLOW   = REGULINCHI!
- RED      = MAL ASUNTO... pero malo malo!
             
En el Opensearch tenemos/guardamos Documentos en LUCENES agrupados en un INDICE.

Al final, el Opensearch es un conjunto de LUCENES.

En un cluster... con cuántos lucenes acabo? DECENAS -> CIENTOS

Esos Lucenes siempre pueden arrancar? NO
Por qué motivo no arrancaría un Lucene?
- Porque no haya ningun nodo dispuesto a correr ese Lucene

Y eso por qué puede pasar? Por qué un nodo puede decidir no ejecutar un lucene?
- Qué no tenga suficiente espoacio en DISCO
- Porque ese nodo ya tenga el primario u otra réplica de ese mismo lucene.

NODO1
    IndiceA-Primario1
    IndiceA-Replica2
    IndiceA-Replica3
    IndiceA-Replica4
NODO2
    IndiceA-Primario2
    IndiceA-Replica1
NODO3
    IndiceA-Primario4
    IndiceA-Primario3

INDICEA: Quiero 4 primarios y 1 réplica. En total cuáns shards tiene ese INDICE A = 8

INDICEB: Quiero 1 primario y 4 réplica. En total cuántos shards tiene ese INDICE B = 5

NODO1
    IndiceB-Primario1
NODO2
    IndiceB-Réplica1(1)
NODO3
    IndiceB-Réplica2(1)


    IndiceB-Réplica3(1) -> NINGUNO (Se queda sin asignar a nodo)
    IndiceB-Réplica4(1) -> NINGUNO (Se queda sin asignar a nodo)

    El cluster se pondría de color: AMARILLO: YELLOW... 
        Está cumpliendo con lo que hemos pedido (Tener 1 primario y 4 réplicas? NO)
        RTengo acceso a todos los datos? SI


    GREEN: Si todos los shards primarios y réplicas están asignados a nodos del cluster.
    YELLOW: Si todos los shards primarios están asignados a nodos del cluster, pero alguna réplica no está asignada a ningún nodo.
     Tengo acceso a todos los datos? SI
     Pero no estoy cumpliendo con la HA solicitada.
    RED: Si algún shard primario no está asignado a ningún nodo del cluster.
     Directamente en este caso NO TENGO ACCESO A LOS DATOS NECESARIOS = JODIDO!

NODO 1 (Pero este nodo tiene el disco duro al 99%)
    INDICE A- Primario1
NODO 2 (Pero este nodo tiene el disco duro al 99%)
    INDICE A- Réplica1(1)
NODO 3 (Pero este nodo tiene el disco duro al 99%)
    INDICE A- Réplica2(1)


    INDICE B- Primario1. Dónde lo pongo? NO HAY HUEVOS... está el HDD petao!
    No hay forma de acceder a los datos del INDICE B. El cluster se pondría de color: ROJO: RED



INDICE A (2 primarios con una réplica cada uno) = 4 shards

NODO 2
    INDICE A - Primario1 ----+
NODO 3         Replica1(2)   |
    INDICE A - Primario2     | copiarlos
             - Replica1(1) <-+

    Y si hago eso, sabéis que va a pasar, en qué estado acabo? RED! EIN???? RED!!!!??? Cómo red???
    Eso está guay... desde el punto de vista teórico se debería de poner en GREEN, porque todos los primarios y réplicas están asignados a nodos del cluster.

    En problema es que cuando empiece a copiar 80Tbs de datos por red de un nodo a otro, y del otro al 1... REVIENTO EL SISTEMA...
    Y LO DEJO FRITO !
        - Peto la RED
        - Peto los HDD
        - Los OS no responden a queries.
        - RED!

    Depende cómo configure OS, puede tratar de hacer esto o le puedo instruir a que no lo haga.
    De hecho, si los datos no los tuviera en el HDD del Nodo1, y los tengo en una CABINA DE ALMACENAMIENTO...
    Mucho más barato, y rápido sería levantar OpenSearch en otro nodo y montarle el mismo volumen que tenía el NODO1... a todos los efectos seria el NODO1 (aunque se llame NODO4)... pero como tiene los mismos datos que el nodo1... en la práctica le sustituye sin problema. Y SABEIS QUIEN ME REGALA ESTA FUNCIONALIDAD? KUBERNETES !!!!!!
    Pero en vuestro caso, ni la usais. Nos da igual... no mejora nada!

    Si se cae un nodo -> CLUSTER -> YELLOW... sigo operando con normalidad? SI
    Puedo mover el shard primario a otro nodo? SI... que gano funcionalmente? NADA

    Y si se cae el segundo nodo? -> RED
    Y ya no puedo operar con el cluster. VALE. Lo aceptamos de buen grado.

    Cuando hago una instalación y defino la política de ALTA DISPONIBILIDAD de un cluster, tomo decisiones.
    ME LA JUEGO A QUE CAIGA 1 nodo. ACEPTO y sigo trabajando con normalidad.
    ME LA JUEGO A QUE CAIGA 2 nodos. PUES ESTOY JODIDO... Qué probabilidades hay de que estoy ocurra? BAJA. ACEPTO EL RIESGO
     Puede ser el srvicio TAN CRITICO que no acepte ese riesgo... y diga.. aunque se caigan 2 nodos, quiero que el cluster siga operando. VALE.. COMPRA UNA MAQUINA MAS DE RESERVA.. que de normal la tienes SIN EJECUTAR TRABAJO. 
     Por si sea alguna otra, que esa asuma el trabajo => PASTIZAL!
     La HA es cara... y cuanta más HA quieras ---> €€€€€€

    3 nodos en Asturias. SI HAY UN TERREMOTO O UN CERO DE ELECTRICIDAD
    3 nodos en Almeria



GREEN!!!!!!!


---



El cambio lo escribo en un fichero de código!
-> GIT
    -> JENKINS(Argo, GitlabCI/CD)
        -> PUT

---

  "number_of_nodes":
  "number_of_data_nodes":

El tema es que en un cluster de Opensearch hay nodos... pero no todos los nodos tiene porque hacer las mismas funciones.
En Opensearch esaas funciones se llaman ROLES.
Y cada nodo puede tener asignados distintos roles.
En VUESTRO CASO, ahora mismo, Los 3 nodos que tenéis asumen los mismos ROLES: 
- master
- data
  - hot         INDICES EN VIGOR
  - warm        INDICES MAS ANTIGUOS
  - cold        INDICES QUE NO SE USAN
- ingest
- ml
Esto sobre todo aplica a cluster MUY GRANDES (20+)

Contenidos <1M

Un cluster gordo puede tener MILES DE MILLONES DE DATOS!    
    AMAZON que tiene su catalogo completo de productos indexado...
    Para que los clientes puedan hacer búsquedas rápidas.

    AMAZON que indexa TODAS Y CADA UNA DE LAS BUSQUIDAS SE SE HACEN EN CADA MOMENTO DEL TIEMPO -> BusinessIntelligence
    Y tomar decisiones en tiempo REAL   MILLONES DE MILLONES DE DATOS



---
USUARIO

usuarios

{ 
    "nombre": "María García López", 
    "email": "maria.garcia@example.com", 
    "edad": 28, 
    "ciudad": "Madrid", 
    "bio": "Estudió ingeniería de software apasionada por la inteligencia artificial", 
    "intereses": [
        "IA", 
        "running", 
        "lectura"
    ], 
    "activo": true, 
    "fecha_registro": "2024-01-15" 
}

Dame los usuarios con más de 30 años. NECESITO OPENSEARCH? NO
Puedo tener esos datos en un POSTGRES? SI
Y el postgres me respondería rápido a esa query? SI
    Siempre que: Indexe la columna edad.

Dame las personas cuyo nombre contenga maria, que tal postgres? REGULAR!
    - Mayúsculas/minúsculas
    - Tildes
    - Alguien se puede llamar "Carmen María López Gutiérrez"

"Ingenieros" -> bio
    Ingeniera, debería hacer MATCH? SI
        Qué tal el postgres? FLIPA ! OLVIDATE!

Pero... usando un índice inverso:
    - Tokenización: "ingeniería"
    - Minúsculas: "ingeniería"
    - Raiz: "ingenier"

  - Ingeniera/ingenieros -> ingenier

En el nombre. quiero aplicar tokenización?
    "María García López" SI
Y mayúsculas/minúsculas? SI
Y tildes? SI
Y steeming? Raíz? NO Aquiñ no tiene sentido

    Si busco "María", quiero que salga "Mario" NO
    No quiero que al generar el índice inverso se usen las RAICES DE LA PALABRA.
        maria -> María
              x  Mario

Y el tema se complica!

Y cada campo de ese documento, puede requerir un proceso DIFERENTE para generar el índice inverso.
Dia1... me equivoco... y aplico al campo NOMBRE streeming.
    Van a funcionar bien las búsquedas? NO maria -> Mario
    Cómo lo resuelvo? VOY BIEN JODIDO !
    Tengo que borrar ese índice, crearlo nuevo, con el mapping(donde definimos cómo se indexa cada campo) correcto, y volver a indexar todos los documentos.

Si tengo pocos documentos... serán pocas HORAS !
Si tengo muchos documentos, NO PUEDO NI PLANTEARMELO! (Se puede pasar meses indexando)

Vosotros tenéis mucha suerte. Tenéis 4 datos. (1M de datos... 1 hora)
El problema es que tuviera 10.000.000.000 
    10 Millardos de datos -> 10.000 horas = 416 días = 1 año y 2 meses
    OLVIATE DE REINDEXAR: ESTAMOS BIEN JODIDOS!

Es CRITICO definir unos mappings correctos. A NIVEL DE CADA CAMPO!




---

index    shard prirep state   docs node
usuarios 0     p      STARTED    1 opensearch-nodes-2
usuarios 0     r      STARTED    1 opensearch-nodes-0

Tenemos un índice de usuarios con un primario y una réplica. El primario está en el nodo 2 y la réplica en el nodo 0.

Me va lento de narices las búsquedas., qué hago? Una réplica más: nodo1
Me sigue yendo lento en las bñúsquedas, qué hago? ESTOY JODIDO!
    Puedo hacer otra réplica? NO... no hay nodo donde ubicarla. Todos los nodos ya tendrían un shard para ese primario.
    O METO NODOS o estoy jodido!

Con la misma situación de partida.
Me va lenta la ingesta... el HDD lo pongo a tope.
Qué hago? Meto 2 PRIMARIOS... si meto un primario NO HAGO NADA MÁS QUE QUE VAYA MÁS LENTO!



    NODO 0                  NODO 1                  NODO 2  
    1-r                     2-p                     1-p
    500/seg                 500/seg                 500/seg
                                                    2-r
                                                    500/seg
                                                ---------------
                                                    1000/seg


    NODO 0                  NODO 1                  NODO 2  
    1-r                     2-p                     1-p
    333/seg                 333/seg                 333/seg
    3-p                     3-r                     2-r
    333/seg                 333/seg                 333/seg
-------------              ------------             ------------
    666/seg                 666/seg                 666/seg

    Y ahora tengo el HDD con capacidad para escribir otro 334 /seg en cada nodo.
    Tengo más capacidad de ingesta.
    
    
    CONTENIDOS (MULTIMEDIA) -> INGESTA o de BUSQUEDAS? BUSQUEDAS
        1 primario y 2 réplicas

    LOGS -> INGESTA o BUSQUEDA?   INGESTA
        3 primarios + 1 réplica
    




POST _analyze
{
  "tokenizer": "standard",
  "filter": [
      "lowercase", 
      { "type": "stop", "stopwords": "_spanish_" },
      "asciifolding"],
  "text": "Uña"
}

Cañón
Canón



Multi
Order            -> Keyword
Presentable
Filter           -> Keyword
Searchable       -> text
eIndexable
eKeyword