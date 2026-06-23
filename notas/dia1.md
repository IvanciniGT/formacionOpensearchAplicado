
# Qué es Opensearch?

Indexador + Motor de búsqueda

~~BBDD NoSQL~~

# OpenSearch Dashboards

Analisis de datos
Generador de gráficas / Cuadros de mando

# ElasticSearch

Indexador + Motor de búsqueda que fabrica una empresa llamada Elastic Inc.... Lleva la hueva de aos haciendo ese producto... y otros:
- ElasticSearch (muchas veces decimos Elastic) = Indexador + Motor de búsqueda
- Kibana        Analisis de datos y Generador de gráficas / Cuadros de mando
- Logstash      Ingesta de información a un cluster de elasticSearch

Esas herramientas ERAN Opensource. Hace 2/3 años, Elastic cambió las licencias. Ahora son PRIVATIVAS-
Esto provocó que una empresa grande (AWS) tomase la última versión de esos productos y lanzase desde ella proyectos nuevos manteniendo la licencia Opensource (y de paso, gratuitos).

    Opensource != Gratuito

    Opensource es que puedo ver el código fuente.
    Pero pueden dejarme ver el código y cobrarme por usarlo (REDHAT).

        ElasticSearch -> Opensearch
        Kibana        -> Opensearch Dashboards
        Logstash      -> Datapeper

    Lo normal es no usar solo uno de los productos, sino TODOS... En el mundo Elastic se habla del stack ELK: ElasticSearch + Logstash + Kibana
    (NOTA: Relamente lo deberían haber llamado : LEK = Logstask-> ElasticSearch <- Kibana)

# Para qué se usa esto?

Indexar datos y buscar datos... principalmente CONTENIDOS (CONTENIDOS TV) - Uso minoritario
Monitorización y registro de logs 

En los clientes teneís 2 clusters en paralelo de Opensearch. Uno para contenidos y otro para logs.

# Qué es un Indexador?

Recabar información y ponerla de una forma ORDENADA para acceder a ella de forma RAPIDA / EFICIENTE!
Poder hacer búsquedas que vayan como un TIRO!

Permite recibir documentos y extraer información para explotarla.

## Eso no lo hacen las BBDD Relaionales? Oracle, postgres, mysql, sql server?

Las BBDD son las grandes expertas en almacenar datos y permitirnos recuperarlos de forma muy eficiente. 
Llevan décadas haciéndolo.

Que tienen dentro (que usamos/creamos) en las BBDD para poder hacer búsquedas sobre los datos de forma muy eficiente? INDICES.

Las BBDD crean índices (o nosotros los creamos en las BBDD) para optimizar las búsquedas.

> Ejemplo: Tabla de recetas de cocina:

| ID   | Nombre                  | Tipo de plato    | Dificultad  | Tiempo de preparación  |
|------|-------------------------|------------------|-------------|------------------------|
|    1 | Tortilla de camarones   | Entrante         | Media       | 15                     |
|    2 | Corderito asado         | Principal        | Media       | 240                    |
|    3 | Gazpacho                | Entrante         | Baja        | 25                     |
|    4 | Bacalao al pilpil       | Principal        | Alta        | 120                    |
|    5 | Tortilla de papas       | Entrante         | Media       | 45                     |
|    6 | Croquetas de bacalao    | Entrante         | Media       | 90                     |
|    7 | Ensaladilla rusa        | Entrante         | Media       | 40                     |
|    8 | Papas arrugás           | Acompañante      | Baja        | 30                     |


1M de datos... Alta, Baja, Media... Los baja donde empiezan si la distribución es uniforme (Misma cantidad de A, B, M): 333.333. La media 666.666
En casos donde no hay uniformidad, hace falta estrategias masavanzadas para recopilar las estadísticas... y las BBDD como Oracle me permite elegir eso. 
Por defecto usan el mecanismos simple... pero puedo cambiarlo a usar una tabla de frecuencias.

    Alta   200.000
    Baja:  150.000
    Media: 650.000


Y ahora quiero hacer búsquedas.
Solo tengo la tabla (en papel, que es más o menos igual que tenerla en el HDD).

> BUSQUEDA 1: Dame las recetas que tardo más de 40 minutos en hacer.

Cómo respondo a esta pregunta... Cómo encuentro esas recetas?
Necesito ir fila a fila, mirando los tiempos de preparación a ver si son >= 40 e ir recopilando los que si.

| ID   | Nombre                  | Tipo de plato    | Dificultad  | Tiempo de preparación  |
|------|-------------------------|------------------|-------------|------------------------|
|    2 | Corderito asado         | Principal        | Media       | 240                    |
|    4 | Bacalao al pilpil       | Principal        | Alta        | 120                    |
|    5 | Tortilla de papas       | Entrante         | Media       | 45                     |
|    6 | Croquetas de bacalao    | Entrante         | Media       | 90                     |
|    7 | Ensaladilla rusa        | Entrante         | Media       | 40                     |

Cómo llaman las BBDD a esta operación? FULL SCAN DE LA TABLA.
Si tengo 20 datos... tengo que hacer 20 operaciones.
Si tengo 1M de datos... tengo que hacer 1M de operaciones.

Esto escala? Qué le pasa al rendimiento a la que voy echando más recetas? Empeora linealmente. EL SISTEMA SE DEGRADA UN HUEVO.

El ciencias de la computación decimos que un FULLSCAN es un algoritmo de Orden(n) . Es decir, necesito hacer tantas operaciones como datos tengo que revisar = CAGADA !

> Alternativa?

El problema es que nos gustaría poder aplicar un algoritmo de búsqueda distinto para encontrar datos.. uno que no se degrade.. uno que no sea de Orden(n).
Y hay uno: BUSQUEDA BINARIA.

> BUSQUEDA BINARIA: La que usamos desde 9 años por ahí... cuando buscamos una palabra en el diccionario.

Quiero buscar "castillo" en el diccionario, que hago? Miro una a una?
Lo que hacemos es partir el diccionario a la mitad "Manzana"... MIERDA ME PASE!
En el diccionario hay 20.000 palabras.
Me he pasado.. pero... acabo de un plumazo de quitarme el mirar de Manzana en adelante (10.000)
Se que castillo esta antes... De trozo primero parto a la mitad: 5000 palabras: "Edificio" -> MIERDA ME PASÉ!
Pero al pasarme acabo de quitarme de un plumazo otras 5000 palabras.

    80000
    40000
    20000
    10000
     5000
     2500
     1250
      675
      340
      170
       85
       43
       22
       11
        6
        3
        2
        1 <--- La tengo (17 operaciones para encontrar la palabra entre 80.000)

Aun suplicando el volumen de datos.. para mi es solo una operación más.
Esto es lo que llamamos un algoritmo de Orden(log(n))

Dados n datos, con log(n) operaciones encuenro el dato de interés.

Solo hay un problema... para poder apicar este algoritmo necesito que? LOS DATOS DEBEN ESTAR ORDENADOS!

Qué tal se le da a un ORDENADOR ordenar datos? COMO EL CULO !
De hecho NO LLAMAMOS ORDENADORES a las COMPUTADORAS por su capacidad de ORDENAR datos... sino por su capacidad de PROCESAR ORDENES!

De hecho... una BBDD, y cualquier programa creado por una persona minimamente inteligente JAMAS ordenaría primero datos para aplicar después una búsqueda binaria... SERIA MUCHO MAS PESADO que un FULLSCAN.
Una ordenación (de las mejores posibles) requieren n*log(n) operaciones. Eso son un huevo más que solo n operaciones que es lo que necesito para un FULLSCAN.

Si no tengo los datos ordenados, prefiero 1000 veces el fullscan. Tardo mucho menos que en PREORDENAR para luego aplicar la búsqueda binaria.

Claro.. con un diccionario hay trampa... los datos vienen YA ORDENADOS.
Las recetas me las van a ir creando ORDENADAS por tiempo de preparación? NO SE .. quizás si... quizás no....
Pero si vinieran... incluso si vinieran ordenadas por tiempo de preparación... Qué pasa si quiero buscar por DIFICULTAD! LA JODIMOS!

SOLUCION: INDICES

# Qué es un INDICE?

Una COPIA ORDENADA DE LOS DATOS junto con su ubicación.
En una biblioteca, el índice era un armario lleno de cajones... De hecho eran varios armarios:
- Por autor

    Ficha: Miguel de Cervantes Saavedra:
        - El Quijote -----> Pasillo 17, armario 4, balda 3 (Ubicación)

- Por género
- Por título
    Ficha: "El"
        - El Quijote -----> Pasillo 17, armario 4, balda 3 (Ubicación)

En los libros de papel, lo tengo igual:
    Al final del libro hay un índice... o varios:
        - Recetas por tipo
        - Recetas por ingrediente principal.

En el índice vienen los datos repetidos, escritos otra vez (DUPLICADOS... o triplicados...) y además la ubicación.
    Tortilla de acelgas
    Tortilla de camarones
    Tortilla de patatas     Página 17 (Ubicación)

Creamos índices para poder aplicar BUSQUEDAS BINARIAS. A costa de MAS ESPACIO... los datos se duplican... se escriben una y otra vez.

Las BBDD, igual que las personas, gilipollas no son. Aprenden cómo se distribuyen los datos dentro de la tabla. (qué datos hay, cuántos de cada uno).
Van generando ESTADISTICAS!
Sabiendo que hay muchas más de la a.. y que la A es la primera al ordenar.. el primer corte lo hago a la mitad? NO optimizo.
Las BBDD también hacen esto.. y si tienen buenas estadístcias pueden ahorrarse 2 o 3 cortes.

LAS BBDD son unas MAGAS de los ÍNDICES... llevan décadas haciéndolo. 
Entonces: PARA QUE LECHES QUIERO UN INDEXADOR?

Esto funciona para ciertos tipos de búsquedas:
Las recetas de dificultad ALTA
Las recetas de tiempo de preparación >= 40 minutos

En estas búsquedas ese tipo de índices funciona bien.

Pero y qué pasa con estas otras búsquedas:

> BUSQUEDA 1: Dame las recetas de bacalao < BUSQUEDA DE TEXTO COMPLETO: FULL-TEXT

| ID   | Nombre                  | Tipo de plato    | Dificultad  | Tiempo de preparación  |
|------|-------------------------|------------------|-------------|------------------------|
|    1 | Tortilla de camarones   | Entrante         | Media       | 15                     |
|    2 | Corderito asado         | Principal        | Media       | 240                    |
|    3 | Gazpacho                | Entrante         | Baja        | 25                     |
|    4 | Bacalao al pilpil       | Principal        | Alta        | 120                    |
|    5 | Tortilla de papas       | Entrante         | Media       | 45                     |
|    6 | Croquetas de bacalao    | Entrante         | Media       | 90                     |
|    7 | Ensaladilla rusa        | Entrante         | Media       | 40                     |
|    8 | Papas arrugás           | Acompañante      | Baja        | 30                     |

INDICE ORDENADO POR NOMBRE DE RECETA.
| Bacalao al pilpil       | 1
| Corderito asado         | 2
| Croquetas de bacalao    | 6
| Ensaladilla rusa        | 7
| Gazpacho                | 3
| Papas arrugás           | 8
| Tortilla de camarones   | 1
| Tortilla de papas       | 5

Me vale para buscar las de bacalao? NO...
Puedo aplicar ahí búsqueda binaria para encontrar las recetas que me interesan (las de bacalao)? NO
PUES TENGO UN PROBLEMA !

Y aquñi es donde hacen falta técnicas de indexado más avanzadas.
Algunas BBDD permiten ténicas más avanzadas:
    - Oracle: Oracle Text
    - Postgres: Índices inversos y trigramas

Aún así, NO SON HERRAMIENTAS TAN POTENTES A LA HORA DE CREAR ESOS INDICES COMO SERÍA UN ELASTICSEARCH/OPENSEARCH

# Índice invertido

| Bacalao al pilpil       | 1
| Corderito asado         | 2
| Croquetas de bacalao    | 6
| Ensaladilla rusa        | 7
| Gazpacho                | 3
| Papas arrugás           | 8
| Tortilla de camarones   | 1
| Tortilla de papas       | 5

Podríamos generar un índice inverso aplicando un PROCEDIMIENTO:
Paso 1: TOKENIZACION: Separa tokens por: Espacios, signos de puntuación , parentesis... 
| Bacalao-al-pilpil       | 1
| Corderito-asado         | 2
| Croquetas-de-bacalao    | 6
| Ensaladilla-rusa        | 7
| Gazpacho                | 3
| Papas-arrugás           | 8
| Tortilla-de-camarones   | 1
| Tortilla-de-papas       | 5

Paso 2: NORMALIZACION: Quitar acentos (tildes), quitar mayúsculas, ...
| bacalao-al-pilpil       | 1
| corderito-asado         | 2
| croquetas-de-bacalao    | 6
| ensaladilla-rusa        | 7
| gazpacho                | 3
| papas-arrugas           | 8
| tortilla-de-camarones   | 1
| tortilla-de-papas       | 5

Paso 3: STOP WORDS: Quitar palabras que no aportan valor semantico (SIGNIFICADO)
| bacalao-*-pilpil       | 1
| corderito-asado        | 2
| croquetas-*-bacalao    | 6
| ensaladilla-rusa       | 7
| gazpacho               | 3
| papas-arrugas          | 8
| tortilla-*-camarones   | 1
| tortilla-*-papas       | 5

PAso 4: STREEMING: EXTRACCION DE LA RAIZ SEMANTICA
| bacala-*-pilpil     | 1
| corder-asad         | 2
| croquet-*-bacal     | 6
| ensalad-rus         | 7
| gazpach             | 3
| pap-arrug           | 8
| tort-*-camaron      | 1
| tort-*-pap          | 5

Paso 5: GENERO EL INDICE INVERTIDO:

    asad      2(2)
    bacala    1(1) 6(3)
    corder    2(1)
    croquet   6(1)
    pilpil    1(3)
    ....

Esto es lo que guardo... ese es el índice.
Ahora me llega una búsqueda: Recetas cuyo nombre contenga EL BACALAO!
Y le aplico a la b´suqeda el mismo procedimiento:

EL-BACALAO
*-BACALAO
*-bacalao
*-bacala

Y ahora busco esos términos en el índice invertido... con búsqueda binaria: 
    bacala -> 
        asad      2(2)
        bacala    1(1) 6(3) <--- En el documento 1 y en el 6
        corder    2(1)
        croquet   6(1)
        pilpil    1(3)
        ....

Esto es un índice invertido... que sirven para búsquedas full text.
Esto es un ejemplo... se puede complicar... 
Puedo querer hacer búsquedas fonéticas... que suenen igual
    vaca -> baca

El proceso de indexado para generar un índice invertido es HARTO PESADO! (computacionalmente hablando... chupa mucha CPU)
Lo bueno... una vez hecho, las búsquedas son super rápidas.

Y esto es lo que hace una herramienta como: APACHE LUCENE (Opensource y gratuito)... escrito en JAVA.

Opensearch/ElastiSearch NO TIENEN NI PUÑETERA IDEA DE CREAR INDICES INVERTIDOS.

Entonces... qué es Opensearch(ElasticSearch)...
Un orquestador de LUCENES para tener HA/Escalabilidad.

En un entorno de producción tenemos no un Opensearch... Tendremos un cluster de Opensearch, repartido en distintas máquinas FISICAS.
En un cluster de Opensearch, tenemos cientos de LUCENES.
Opensearch va dando instrucciones a esos lucenes para indexar / buscar.
Opensearch toma los resultados de los lucenes de vuelta, los consolida y los devuelve por http.
Las peticiones a Opensearch también las hago por http.
Con Lucene solo puedo hablar desde JAVA:


    Programa (cliente) ---> BUSQUEDA ---> OPENSEARCH --> Nodo1
                                                            Lucene1
                                                            Lucene2
                                                            Lucene n
                                                         Nodo2
                                                            Lucene1
                                                            Lucene2
                                                            Lucene m
                                                         NodoN
                                                            Lucene1
                                                            Lucene2
                                                            Lucene k


Lucene = SHARD = FRAGMENTO

Índice en OpenSearch tiene varios SHARDS (Lucenes) ... primarios y de replicación.

---

Hemos hablado hasta ahora de lo que es un índice normal (BTREE) y un índice invertido....
Hemos introducido Lucene...
Vamos a seguir rascando:

En Opensearch existe el concepto de INDICE.

Pero... en Opensearch un índice es otra cosa... ni es un índice invertido , ni es un índice BTREE.

# Qué es un índice en OpenSearch?

Y en Opensearch un índice es una agrupación LOGICA de documentos, sobre los que puedo lanzar una búsqueda conjunta.

- Índice de facturas
- Índice de contenidos multimedia (cada contenido que se da de alta en el sistema-> Postgres se gurda aquñi también... indexada y una copia vieja)
- Índice de eventos de postgres (cada linea de cada fichero que ha existido de cada postgres se guarda aquí como un documento independiente)

Es una agrupación LOGICA.

El equivalente en una BBDD Relacional, sería una TABLA.

Cuando hago una solicitud de indexación... Mando una linea de un fichero de log... Mando un json con un contenido multimedia.
Dónde se guarda? Y quién lo guarda? 
Lo guarda LUCENE. Lucene generará un índice para cada tipo de dato de esos documentos

    Linea de un log
    17-08-2026 14:44:21 INFO El sistema está arrancando <- EVENTO, guardado en un archivo de log

    Eso se transforma por FluentD en un JSON (Opensearch solo entiende de JSONs)
    {
        "contenidoOriginal": "17-08-2026 14:44:21 INFO El sistema está arrancando <- EVENTO, guardado en un archivo de log",
        "fecha": "17-08-2026",
        "hora": "14:44:21",
        "nivel": "INFO",
        "detale": "El sistema está arrancando",
        "servidor: "192.168.167.98",
        "fichero": "/var/logs/postgres.log",
        "linea": 178
        y más
    }
    Y esa entrada en log que ocupaba: 51 caracteres -> bytes? UTF-8: 52 bytes
    Se transforma en un documento de 380 bytes
    Que se manda a Opensearch... Y opensearch se lo manda a un lucene.
    Y lucene:
    - Por un lado guarda copia de eso: 380 bytes.
    - Y por otro indexa.
        La fecha: "17-08-2026" -> Esa fecha aparece en el documento CXLA-SDAK-AHSFKAS-129374-81298
        La hora: "14:44:21"    -> Esa hora  aparece en el documento CXLA-SDAK-AHSFKAS-129374-81298
        El nivel INFO:         -> Esa nivel aparece en el documento CXLA-SDAK-AHSFKAS-129374-81298
        ...
        Algunos campos se indexan usando indices tradicionales: FECHAS... INFO
        Otros mediante indices invetirdds: Detalle, servidor...
        Y ese dato, que eran 52 bytes... se transforman en 1kB fácilito!

        Eso es configurable por INDICE: Se define en lo que en Opensearch llamamos los MAPPINGS de un índice.
        Al crear un índice (una colección lógica de documento), le defino unos mappings...
        Donde detallo para cada campo el típo de índice que quiero generar... 
        Y si el campo es especial (TEXTO), defino ... AGARRATE!
            Que procedimiento de indexación quiero: Que tokenizado, que normalizados, que stemmer (si es que lo quiero o no), si quiero búsqueda fonética...
            LA HUEVA DE COSAS! a nivel de cada campo (esto también se hace en un JSON... que fácil para un indice puede acabar con 2000-4000 lineas)
        Si no defino unos buenos mappings (una buena estrategia de indexación) luego las búsquedas irán a pedales!
        Y no bastará con cambiar los mappings (la estrategia de indexación) NECESITARE REINDEXAR TODO! de acuerdo a la nueva politica de indexación.

Pero... hay una cosita más.


    Opensearch lo voy a instalar en varias máquinas... cluster... para que si se jode una máquina, pueda seguir dando servicio.

        Nodo1
            Opensearch
                Lucene1 original
                Copia Lucene2
        Nodo2
            Opensearch
                Lucene 2 original
                Copia Lucene3
        Nodo3
            Opensearch
                Lucene 3 original
                Copia Lucene1

Y ahora quiero guardar la linea 1 del fichero de log de apache/postgres.. el que sea.
Quién guarda al final eso? Quién indexa?
Qué lucene? En qué máquina estará ese Lucene?

Pero... cuántos eventos de log me llegan? 4? cientos o miles por minuto
Y llegara un momento que un componente de hardware dirá hasta aquí! No doy más a basto:
    - HDD
    - CPU
    - RED

Qué hago en este caso? Meter más lucenes en paralelo.
Esto se determina mediante monitorización. NO HAY MAGIA.

Y entonces, llegamos a otra conclusión:
- Un índice de Opensearch es una colección / agrupación LOGICA de documentos
- Un índice de Opensearch es una colección de Lucenes (en téminos de OS= Shards)
    En nuestro caso, nuestro índice de los logs del postgres tiene :
        - 3 shards primarios (cada uno guarda documentos distintos a los demás)
        - Y cada primario, tiene una réplica (que guarda los mismos documentos que el primario del que es réplica) 
    En total nuestro índice tiene / gestiona 6 fragmentos (shards = lucene)

    Si necesito más escalabilidad en escritura, que me interesa aumentar? PRIMARIOS (para repartir más el trabajo, ya que guardan documentos distintos entre si)
    Si necesito más escalabilidad en lectura, que me interesa aumentar? REPLICAS (para tener más sitios paralelos de donde sacar el mismo dato)

    Cómo se cuantos? Os apuntais al curso de avanzado en la siguiente edición!


Un backup se hace de los shards primarios (de todos). Y de ese backups quieres DUPLICACION!

    Haré un backup del sistema el lunes.  Pero este le guardo duplicado.
    Haré un backup del sistema el martes. Pero este le guardo duplicado.

---

Google indexa páginas web y os permite hacer búsquedas sobre ellas.
Pregunta. Google guarda las páginas WEB? A priori no debería de guardarlas.
Solo guarda un INDICE (realmente muchos) que permitan hacer busquedas sobre las webs.
Y cuando hago búsqueda me da un resultado: 

UBICACION! LA URL de la página

Lo que pasa es que Google también se queda con una copia de la web... en el momento de indexarse.
El dato real donde está? La versión actual de la web? En google? NO
La web actual estará alojada en un servidor... fuera del control de google.

Para qué guarda google una copia de la web? Mostrar CONTEXTO EN LA BUSQUEDA!

Puede ser que cuando entre en la web real, no aparezca el término?

La web se indexó hace 3 días... y google genera indices.. y queda con una copia...
Y hago búsqueda y la búsqueda es sobre los indices de google.. y el contexto que se muestra es en su copia de los datos de la web.
Si los administradores de la web la han cambiado hace 30 minutos... puede que al entrar no vea el dato... lo hayan quitado.

Una cosa es el dato original/vivo y otra los indices de búsqueda... que pueden estar desactualizados.

Mis datos los tendré en un Oracle, Postgres... Ahí es donde está la ultima versión, la viva.
En paralelo, solicito a Opensearch que indexe el dato... para tener búsquedas más potentes, más rápidas...
Opensearch me devolverá el ID del del documento en Oracle + contexto... porque opensearch también guarda una copia del documento/dato en el momento de la indexación.
Y luego si quiero el detalle, ya entro en Oracle.

Oracle, Postgres están pensados para un uso TRANSACCIONAL (Con tablas vivas)
Opensearch no está pensado para eso... Las indexaciones SON PESADAS! Tardan mucho.

---

Logs... Y los logs son diferentes en su comportamiento con respecto a los contenidos.

    Logs son documentos muertos
    Los contenidos son documentos vivos.

    Puede cambiar la descipción de un contenido? SI
    Puede cambiar la fecha? El mensaje, La severidad de una entrada que se escribió en un log? NO ES UN EVENTO(FECHA) PASADO!
    Por definición es inalterable!

    Puede cambiar una métrica que medí de uso de CPU de un servidor? NO.. podrá cambiar el valor actual de esa métrica.. pero el valor que medí ayer a las 15:04 es un evento pasado.. que ya no cambia.
    El documento cuando se produce YA NO PUEDE CAMBIAR... es inalterable... no está vivo... esta muerto! NO CAMBIA!

    Un contenido, se carga hoy... mañana se dita, pasado otra vez... Tengo formularios para editarlo.
    Un contenido no es un EVENTO... es una ENTIDAD! que existe, que es, con independencia del momento del tiempo.

Y aquí occure algo especial. Si el documento ya no cambia (LOG)... y Opensearch guarda una copia en el momento de la indexación...
Esa copia que guardó opensearch será igual a la copia vigente? Al valor actual?  SI... porque no cambia.. por definición. por ser un evento.
Si el documento puede cambiar (CONTENIDO)... y Opensearch guarda una copia en el momento de la indexación...
Esa copia que guardó opensearch será igual a la copia vigente? Al valor actual?  NO TIENE PORQUE... OJALA!

Para contenidos, la copia actual la guardo donde? POSTGRES/ORACLE...
Y el indexado de búsquedas?                       OPENSEARCH

Y para logs... el indexado lo guardo en ?         OPENSEARCH
Y la copia actual?                                BBDD? Para qué? si ya opensearch ha hecho una copia y por definición es inalterable.
                                                    Para que necesito otra copia? PARA NADA.
                                                    Y por ende, sin comerlo ni beberlo, Opensearch se acaba de convertir 
                                                        NO SOLO EN INDEXADOR sino en REPOSITORIO DE PERSISTENCIA (BBDD)
Opensearch no es una BBDD... pero a veces(solo a veces, si el documento YA NO VA A CAMBIAR) con la copia que hace es suficiente. 
Y en este caso hace las veces de "bbdd" para dar persistencia al dato.

---

Imaginad que tengo el log de Apache/Postgres/Keycloak... de cualquier herramienta.


Los eventos del log se guardan donde en primera instancia? En un fichero apache-17-08-2026.log

Desde el punto de vista de Opensearch, el fichero NO ES UN DOCUMENTO.
CADA LINEA DEL FICHERO es un documento.
En Opensearch cargo LINEA A LINEA del fichero.

fichero == colección de eventos (que va cambiando con el tiempo).... pero cada evento NO CAMBIA CON EL TIEMPO... Y para Opensearch CADA LINEA es un documento.
Si tengo un archivo de 500.000 lineas... Son Medio millón de documentos que he indexado independdientes en OpenSearch.

Los logs pueden crecer hasta el infinito.
Los contenidos crecerán hasta el infinito? NO.... o si... pero en el tiempo que los humanos vamos a vivir....
Cuántos contenidos sea crearan? No llega al millon en vuestro sistema más grande.
    Me sirven para algo los contenidos creados hace 2 años? SI
    Y estos no los iré borrando.

Y lineas de logs? A efectos prácticos == INFINITO!
   Me valen para algo las lineas de los archivos de log de hace 2 años? Posiblemete no
   Pues estos los iré borrando.

Y para hacer eso fácil, en Opensearch existen lo que llamamos POLITICAS DE CICLO DE VIDA DE INDICES.
Donde definimos que automáticamente cada 90 días, se borren los datos.
Y cosas mucho más complejas:
    Cuando el índice (los datos) tiene 90 días los filtras y te quedas solo con warnings y errores.
    Cuando tienen 1 año, te quedas con la cantidad total de warnings y errores que han ocurrido al día.
    A los 2 años, te quedas con el agregado mensual.
    Y a los 3 años lo borras.

---

La persistencia de los eventos de log no la hacemos en ficheros... la hacemos en Opensearch.

    Tomcat     -> stdout.log
    Keycloack  -> keycloak.log
    Postgres   -> postgres.log
                    Pero estos archivos no se guardan como persistencia.

                    FluentD (Agente Fluent)
                    Esa herramienta está monitorizando en tiempo real esos archivos.
                    Cada linea que se escribe allí se manda al Opensearch.
                    Y en ese momento la linea puede ser eliminada del archivo original. YA NO ME SIRVE PARA NADA.

                    De hecho, lo normal es configurar ROTACION DE ESOS ARCHIVOS.
                    Quiero tener 2 archivos rotados del postgres: postgres1.log y postgres2.log
                    Cuando cualquiera llegue a 50Kbs (o el tamaño que quiera), que se ponga a escribir en el otro archivo.

                    Así limito el espacio en disco que ocupan los logs.
                    Tengo 2 para ir dando tiempo al Fluent a que vaya leyendo, antes de que se machaque el archivo.

                    El fluentd los manda a Opensearch... y allí se guardan juntos. Mientras así esté configurado en la politica de ciclo de vida del índice.
                    Y esto tiene una ventaja enorme.

                    Si tengo 10 tomcats, 1 keycloak, 3 postgres... el rabbit.. y demás...
                    Cuantos ficheros de log tengo que estar monitorizando yo HUMANO? Imposible!
                    No monitorizamos sobre esos ficheros de log... Monitorizo sobre el INDICE en Opensearch...
                    que tiene los datos de los archivos de log de TODOS LOS SERVIDORES Y SERVICIOS consolidados.

                Opensearch Dashboards se activa u filtro que busca si en linea aparece la palabra ERROR, error, Error


---

NOTA: Sobre el almacenamiento

El almacenamiento es caro o barato hoy en dia? ES DE LAS COSAS MAS CARAS EN UN ENTORNO DE PRODUCCION!

Pienso que es barato... claro.. yo voy al mediamarkt que no soy tonto y me compro un HDD para mis fotos de 2Tbs por 60€.
Si. un western blue.

Un disco de calidad profesional que aguente muchas lecturas / escrituras son un x10 en el precio... fácil

Pero espera... De cada dato, cuantas copias hago en un entorno de producción? 1 = SUICIDIO! NI DE BROMA
  Al menos 3... Esos 2 Tbs.. = 50€ x 10 => 500€ x 3 = 1500€
  Y ahora... mete backups

  Las réplicas no es backups... es Alta disponibilidad. Si un HDD se jode (dios no lo quiera) que pueda seguir accediendo al dato.
  Pero si un manazas mete la pata y borra algo, el borrado se hace en las 3 réplicas!

  Y necesito copia independiente para recuperación ante desastres (dios no lo quiera).
  Y ese backup... al menos lo guardaré en 2 sitios!
  Y no tendré uno... tendré backups al menos de 2 semanas atrás.

Y esos 2Tbs, que en mi casa son 50€, en la empresa fácil se convierten en 5000€.
Y NO ME ENTRA EN LA CABEZA ! FLIPO!

El almacenamiento es MUY CARO!


---