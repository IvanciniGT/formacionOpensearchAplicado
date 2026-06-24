
# Repaso rápido:

Ejecutar algunas peticiones contra nuestro cluster de Opensearch.
Lo hicimos con ayuda al Opensearch Dashboards (DevTools).

    - Salud del cluster (Aprovechamos para entender los estados de un cluster: Green, Yellow, Red)
    - Creando índices, con settings y mappings personalizados.
    - Analizando ANALIZADORES sintácticos:
      - Tokenizadores
      - Filtros: Acentos, Stopwords, Stemming, case
    - Mirando el impacto en las búsquedas.
  
---

- Alias + Politicas de ciclo de vida de índices + Plantillas de índices
- Queries DSL, agregaciones, análisis de datos.
- Opensearch Dashboards: Discovery

---

# Alias + Políticas de ciclo de vida de índices + Plantillas de índices

Hay índices que pueden crear hasta el infinito y más allá.. en especial los de logs.

> A priori podriamos pensar que lo hacemos es como haríamos en un Oracle.
> Tener una tabla grande... y de vez en cuando ir borrando cosas de ella (por fecha)

Traducido al Opensearch: Me creo el INDICE: logs-de-apache y le cargo ahí datos.. y todos los meses borro los datos que tengan más de 3 meses de antigüedad.

Eso no sería nada eficiente.

Lucene va generando los índices (directos + índices invertidos) y los guarda en archivos... Esos archivos se llaman archivos de segmento.
En los archivos de segmento solo vamos añadiendo cosas al final. Si un documento es editado (cosa que no pasa con los logs, si pasa con con los contenidos), realmente Openseach lo que hace es generar un registro totalmente nuevo y marcar el anterior como eliminado. Los archivos de segmento no se pueden modificar, solo añadir cosas al final.
Pero realmente el dato/registro/documento no se borra de los archivos.
Eso pasa igual al borrar un documnento. Si borro un documento, el documento no es borrado de los archivos de segmento, sino que se marca como eliminado. Los archivos de segmento no se pueden modificar, solo añadir cosas al final.

Esto provoca que esos archivos , aunque yo borrase datos del índice, crezcan hasta el infinito. No podemos plantearlo.
Hay operaciones que nos ayudan a reescribir estos archivos completamente. Eso es un proceso DESEABLE:
- En ese proceso se borran físicamente los documentos que se hubieran marcado como eliminados. -> LIBERA ESPACIO
- Se reescriben los archivos de segmento, eliminando fragmentación y optimizando la búsqueda. -> MEJORA EL RENDIMIENTO + LIBERA ESPACIO.


Me han llegado documentos de recetas... en cuyo campo NOMBRE vienen estos datos
Esos documento (8) han llegado en unos segundos/minutos. 8:00-> 8:05
| Bacalao al pilpil       | 1
| Corderito asado         | 2
| Croquetas de bacalao    | 6
| Ensaladilla rusa        | 7
| Gazpacho                | 3
| Papas arrugás           | 8
| Tortilla de camarones   | 1
| Tortilla de papas       | 5

Lucene genera el índice invertido:

    asad      2(2)
    bacala    1(1) 6(3)
    corder    2(1)
    croquet   6(1)
    gazpach   3(1)
    papas     8(1)
    pilpil    1(3)
    rus       7(1)
    tortilla  1(1) 5(2)
    ...

Esa información: INDICE INVERTIDO, se guarda en archivos de segmento.

Pero ahora vienen otros 5 documentos:
| Bacalao o brasa         | 9
| Corderito al horno      | 10
| Croquetas de jamón      | 11
| Ensaladilla de marisco  | 12
| Salmorejo               | 13

Y se genera índice inverso:

    bacala   9(1)
    bras     9(1)
    corder   10(1)
    croquet  11(1)
    ensal     12(1) 
    salmor    13(1)
    ...

Eso se guarda o bien en un nuevo archivo de segmento.. o bien al final del archivo de segmento anterior (si hay espacio suficiente). Pero no se reescribe el archivo de segmento anterior.

---

    asad      2(2)
    bacala    1(1) 6(3)
    corder    2(1)
    croquet   6(1)
    gazpach   3(1)
    papas     8(1)
    pilpil    1(3)
    rus       7(1)
    tortilla  1(1) 5(2)
    ---
    bacala    9(1)
    bras      9(1)
    corder    10(1)
    croquet   11(1)
    ensal     12(1) 
    salmor    13(1)

---

Hay términos repetidos.
Al hacér la búsqueda, Lucene debe buscar en cada uno de esos trozos... de cada archivo de segmento. Eso pierde mucho la gracia de Lucene.

    Esto tiene 2 problemas:
    - Ya no es SOLO una búsqueda binaria... Es una búsqueda binaria en cada uno de los archivos de segmento (o trozos)
    - Los términos aparecen repetidos... esto engorda los archivos de segmento y necesito mas HDD.

La situación ideal cuál sería?
 > Acabar con un único fichero de segmento, que contenga todos los términos, sin repeticiones y sin fragmentación, y de paso, sin elementos marcados como eliminados (pero ocupando el mismo espacio que antes).
 (Más o menos ideal... luego habrá por ahí otros factores a tener en cuenta: BACKUPS)

Opensearch puede hacer eso. Es una operación que se llama MERGE. Él va haciendo sus propios merge... según algunas reglas automatizadas. Pero podemos forzar un MERGE manualmente, diciendo que me deje todo consolidado en un único archivo de segmento.


Ahora bien... esto tiene pinta de ser una operación sencilla o una operación que va a tardar un buen rato? Si tengo 10 archivos de 1Gbs a consolidar...

Es una operación costosa... y lo peor no es que sea costosa.,. es que al día siguiente que pasa? OTRA VEZ DESMADRE!

Cuándo me interesaría hacer esa operación? Cuál sería un buen momento? Cuando ya no voy a escribir absolutamente NADA MAS EN ESE INDICE. En ese caso, le aplico el superMERGE del 15. No importa si tarda un poco o un poco más... porque ya no voy a escribir nada más en ese índice.... el resultado es PERMANENTE.

Lo que pasa... es que nosotros vamos a dejar de escribir logs de apache alguna vez? NO

SOLUCIÓN: VAMOS A TENER NO UN INDICE DE LOGS DE APACHE. Vamos a crear un índice de logs de apache cada Día/Semana/Mes... Vuestra unidad de tiempo favorita! (realmente hay criterios para determinar cada cuanto debo crearlo.)

    indice-logs-apache-enero-2026
    indice-logs-apache-febrero-2026
    indice-logs-apache-marzo-2026
    indice-logs-apache-abril-2026
    indice-logs-apache-mayo-2026
    indice-logs-apache-junio-2026


    Los logs son editables? NO
    
    Llegado el 1 de marzo... Voy a tener en algun momento necesidad de escribir más en la vida en el índice de febrero? NO.
    Podré hacer búsquedas... pero escribir NO: CONGELO EL INDICE DE FEBRERO.
    Lo que hago es aprovechar ese momento en el que marco el índice como CONGELADO (solo lectura) para hacerle un MERGE y dejarlo en un único archivo de segmento, optimizado y sin fragmentación. Y eso hará que las búsquedas sean AUN MAS EFICIENTES y que el espacio en disco sea el mínimo posible. CONSECUENCIA DE HABERLO DESFRAGMENTADO.

    Es más... si está congelado... voy a tener mucha ingesta? NINGUNA!
    Y si voy a tener poca ingesta, quizás me interese tener cuántos shards PRIMARIOS? 1
    Y réplicas? Depende.. si va a tener muchas lecturas: 2 o 3 (en vuestro cluster que tiene 3 nodos... como mucho 2)
    Si no tiene muchas búsquedas.. con 1 réplica para cubrir la HA me es suficiente.

    Esto es lo normal...
    En cierto punto quizás me interese CERRAR el índice. CERRAR != CONGELAR.
    Sobre un índice CERRADO no puedo ni hacer escrituras, ni búsquedas... SOLO LO DEJO COMO MATERIAL DE ARCHIVO... por si acaso algún día necesito volver a hacer una búsqueda ahí (Tendría que REABRIRLO)

Estas operaciones no las hacemos a mano. Las automatizamos. Para eso tenemos las POLÍTICAS DE CICLO DE VIDA DE ÍNDICES (ILM: Index Lifecycle Management)

Defino estados, Defino transiciones de estados, defino las acciones que deben ejecutarse (congelar, mergear...) cuando se llega a un estado, y el patrón de índice al que se aplica esa política (apache-logs-*). Y Opensearch se encarga de ejecutar esas acciones cuando se cumplen las condiciones.

Cúantos índices de apache-log voy a tener? 1? NO... iré creando índices cada mes.
El índice de cada mes, cuando se congele y mergee, tendrá 1 solo archivo de segmento interno.
Pero índices tendré 1 por mes.

En la política de ciclo de vida, también posiblemente los vaya borrando... 
Después de 12 meses DIRECTO LO BORRAS.

En un momento dado, tendré:
    ~~apache-logs-diciembre-2025      ELIMINADO~~
    apache-logs-enero-2026          CERRADO          Pocos (Incluso 1).. depende de la estrategia de mergeo que haya definido 
    apache-logs-febrero-2026        CERRADO          Pocos (Incluso 1).. depende de la estrategia de mergeo que haya definido 
    apache-logs-marzo-2026          CERRADO          Pocos (Incluso 1).. depende de la estrategia de mergeo que haya definido 
    apache-logs-abril-2026          CONGELADO        Pocos (Incluso 1).. depende de la estrategia de mergeo que haya definido 
    apache-logs-mayo-2026           CONGELADO        Pocos (Incluso 1).. depende de la estrategia de mergeo que haya definido 
    apache-logs-junio-2026          VIGENTE          Montón de archivos de segmento


La pregunta es:
   Cuando cargo datos:, hago un POST del JSON al índice...
   A qué índice? Tengo un nombre fijo? NO
      En FluentD tengo que calcular el nombre del índice en base al mes.

      Y si el día de mañána quiero guardarlos por semanas? Tendré que cambiar la politica en Opensearch Dashboards.. y además: CAMBIAR EN FLUENTD el algoritmo que determina el nombre del índice (ya no es por meses... ahora por semanas)

      ESTO DESDE EL PUNTO DE VISTA DE DISEÑO/ARQUITECTURA DE SOFTWARE ES UN SUICIDIO!

      Estoy acoplando el programa de ingesta a la POLITICA que defino el Opensearch.
      Lo que implica que si cambio la politica, tengo que cambiar el programa de ingesta. 
      Y si no lo hago, explota! Y NO CARGA DATOS.

      NO TRABAJAMOS ASI!!!! JAMAS EN LA VIDA.

Mismo problema, otra variante:

Quiero un dashboard que muestre el número de errores en el log de apache del mes actual.
Contra que índice trabajo? apache-logs-junio-2026
Y el mes que viene? VETE A CAMBIARLO AL DASHBOARD.

Y para resolver esta situación, EN OPENSEARCH existe el concepto de ALIAS!
Un índice tiene un nombre... pero puede tener 500 alias. Además un alias puede a su vez apuntar a 500 índices.

    apache-logs-enero-2026          CERRADO          apache-logs
    apache-logs-febrero-2026        CERRADO          apache-logs
    apache-logs-marzo-2026          CERRADO          apache-logs
    apache-logs-abril-2026          CONGELADO        apache-logs
    apache-logs-mayo-2026           CONGELADO        apache-logs
    apache-logs-junio-2026          VIGENTE          apache-logs apache-logs-vigente

Esos alias, puedo establecerlos en AUTOMATICO, en la POLITICA DE INDICES,COMO OTRA ACCION,igual que congelar,mergear,borrar...

En fluentD configuro que la carga se haga en el índice: apache-logs-vigente

En el dashboard, los errores del mes actual, los saco del índice: apache-logs-vigente
Y si quiero los errores totales de los últimos meses de apache:   apache-logs
    Y al poner este alias, se buscaría en :
            apache-logs-abril-2026          CONGELADO        apache-logs
            apache-logs-mayo-2026           CONGELADO        apache-logs
            apache-logs-junio-2026          VIGENTE          apache-logs apache-logs-vigente

Los índices tienen un nombre.
NUNCA JAMAS EN LA VIDA, BAJO NINGUN CONCEPTO; NI. ME LO PLANTEO PON UN SEGUNDO uso un nombre de índice en ningún SITIO.
Siempre uso ALIAS.

En los dashboards: ALIAS
En las ingestas: ALIAS
En lo que sea: ALIAS

---

Otro ejemplo.

> Tengo un índice de contenidos (Multimedia) : TEDIAL

Este índice interesa generarlo por meses? NO
Por qué? No aprovecho la política.... 
Puedo editar un dato de enero en junio? SI
Puedo borrar un dato de marzo en abril? SI

Aquí no hay gracia en una politica. CERRAR/CONGELAR/MERGEAR

Cuántos índices quiero en un caso como este? 1 SOLO INDICE.

Tiene gracia entonces aquñi trabajar con ALIAS? TIENE SENTIDO? SI
NUNCA JAMAS EN LA VIDA, BAJO NINGUN CONCEPTO; NI. ME LO PLANTEO PON UN SEGUNDO uso un nombre de índice en ningún SITIO.
Siempre uso ALIAS.

IndiceContenidos
    Creado con unos mappings que pensaba yo el día 1 que eran guays.. pero MIERDA PA MI.. las búsquedas son RUINA!

Hay que reindexar el índice. Que significa eso? 
    BORRO EL INDICE VIEJO y CREO UNO NUEVO DESDE CERO, CON NUEVOS MAPPINGS al que LE CARGO TODOS LOS DOCUMENTOS DE NUEVO.

    IndiceContenidosV1      
        mappingsV1
    IndiceContenidosV2
        mappingsV2
    IndiceContenidosV3
        mappingsV3
    IndiceContenidosV4      alias: IndiceContenidosVigente
        settingsV2 (quiero más primarios)

    A qué índice cargo?                 IndiceContenidosVigente
    Sobre qué índice hago Dashboards?   IndiceContenidosVigente

# Index templates

Plantillas de índices.

Esto aplica a casos como el del apache.
No tengo solo un índice de Apache... Tengo uno cada mes..
Todos quiero que tengan la misma configuración: mismos primarios, mismas réplicas.. mismos mappings, mismos analizadores, mismos filtros, mismos tokenizadores...

No defino los mappings y los settings en cada índice... 
Genero una plantilla de índice, y cuando se crea un nuevo índice, automáticamente se le aplican los settings y mappings de la plantilla.

La plantilla de indice tiene un nombre... y además un patrón de índice al que se aplica.

Podría tener una plantilla llamada: "plantilla-logs-apache" 
que se aplique a todos los índices cuyo nombre sea: "apache-logs-*" (ESTE ES EL PATRON)
Y a esa plantilla le pongo mappings, settings.
Y cualquier índice que sea creado con un nombre que encaje en el patrón, automáticamente se le aplicarán los mappings y settings de la plantilla.

CUIDADO CON ESTO.

A veces, como me despiste, hago un cambio de settings o mappings en un INDICE CONCRETO... y al mes siguiente estoy jodido. 
Lo debía haber hecho en la plantilla de índice, y no en el índice concreto.

---

# Queries

Opensearch tiene su propio lenguaje de consultas. Se llama DSL (Domain Specific Language). Es un lenguaje específico para hacer consultas en Opensearch.

Lo escribimos en JSON. Es un lenguaje muy potente, pero a veces es un poco complicado de entender.

{
    "query": {
       // detalle de la query
    }
}

Lo que tendremos son algunas palabras clave: query, filter, must, should, must_not, match, term, range, bool, etc.

# match vs term

match -> búsquedas de texto completo. Se aplica a campos sobre los que hayamos generaado un índice invertido. 
        Se aplica a campos de tipo TEXT. Se aplica a campos que han sido analizados (tokenizados, filtrados, etc.)
        En automático al usar esta palabraa, Opensearch va a analizar con el mismo procedimiento que el campo sobre el que hago la búsqueda (tokenizador, filtros,...) el texto que le pasemos, y va a buscar los términos en el índice invertido.
        NOTA: Si lo aplico sobre un campo JEYWORD, como a ese campo no se le aplica análisis ninguno,al termino de búsqueda tampoco.
term -> búsquedas exactas. No se le aplica transformación al valor suministrado. Se suele aplicar a campos de tipo KEYWORD.
       Opensearch va a buscar el texto que le pasemos tal cual en el índice.

---

"nombre": "Pedro García Sanchez"

Lo hemos indexado como texto, aplicando algunas actividades de tokenización y filtrado.

    "pedro"         DOC1(1)
    "garcía"        DOC1(2)
    "sanchez"       DOC1(3)

    term -> pedro

    "Pedro García Sanchez"


    federico.sanchaz@miempresa.com

email
    keyword -> me lo deja como esta en el índice invertido.         federico.sanchaz@miempresa.com
    .dominio -> Con lo que está después del @                       miempresa.com        


Cualquier campo de tipo texto, opensearch siempre hace por defecto:
    - TEXT (analizador por defecto)
    - .raw (no analizado, tipo keyword)

PERO YO SUELO QUERER CAMBIAR ESO SIEMRRE!


BIOGRAFIA
    - TEXT (analizador custom) (STEMMING)

NOMBRE
    - TEXT (analizador custom) (NO STEMMING)
    - .raw (no analizado, tipo keyword)
CIUDAD
    - TEXT (analizador por edge-ngram) AUTOCOMPLETE
    - .raw (no analizado, tipo keyword)

NO ME FIO DE LO QUE HAGA EL OPENSEARCH. SIEMPRE LO CAMBIO

IDs de CONTENIDOS MULTIMEDIA

    "12082016/MADRID/0010289290284"
        Keyword
        .fecha date format: ddmmyyyy
        .provincia

---
RANGOS:

    gte -> greater than or equal
    gt  -> greater than
    lte -> less than or equal
    lt  -> less than

Por ejemplo,en nuestro campo edad:

    {
        "query": {
            "range": {
                "edad": {
                    "gte": 30,
                    "lte": 40
                }
            }
        }
    }

# Cómo combinarlos

Aquí sale una palabra importantísima: bool

Bool se usa en combinación con otras palabras:
- must          Reglas que se deben cumplir SI O SI, SE TIENEN EN CUENTA EN EL RANKING (ORDEN, RELEVANCIA)
- filter        Reglas que se deben cumplir SI O SI, NO SE TIENEN EN CUENTA EN EL RANKING (ORDEN, RELEVANCIA)
- should        Reglas que me gustaría que se cumplieran, PERO NO SON OBLIGATORIAS. SI SE CUMPLEN, MEJOR PARA EL RANKING (ORDEN, RELEVANCIA)
- must_not      Es como el FILTER pero en negativo. Son reglas que NO SE DEBEN CUMPLIR SI O SI, NO SE TIENEN EN CUENTA EN EL RANKING (ORDEN, RELEVANCIA)

Y puedo poner varias de esas palabras en un mismo bool.

{
    "query": {
        "bool": {
            "must": [
                { "match": { "nombre": "Pedro" } },
                { "match": { "apellido": "García" } }
            ],
            "filter": [
                { "range": { "edad": { "gte": 30, "lte": 40 } } }
            ]
        }
    }
}

Con must lo importante es lo que pongo en el filtro.
Si pongo un filtro que o se cumple o no se cumple (BINARIO) el score va a ser el mismo. NO TIENE SENTIDO USAR MUST.
Puedo usarlo.. pero no hay diferencia práctica entre usar MUST o FILTER.
Lo uso solo cuando el filtro que pongo dentro del MUST se puede cumplir en mayor o menor medida:
                    "match": {
                      "nombre": {
                        "query": "pedro moreno",
                        "operator": "or"
                      }
                    }
        Puede ser que un dato tenga pedro
        Puede ser que un dato tenga moreno
        Puede ser que un dato tenga pedro y moreno

Hay otro tema. 
- Cuando uso filter, Openmsearch tiene la posibilidad de cachear el resultado del filtro.
- Opensearch NUNCA cachea el resultado de un MUST. Siempre lo tiene que calcular de nuevo, para calcular el score. Y eso es mucho más costoso.

En algunos casos, hemos visto que poner filter o must daba el mismo resultado en la práctica (al final a todos les pone el MISMO score... a unos 0 -filter- y a los otros 1 -must-). 
La cosa es que internamente Opensearch lo calcula de manera diferente. Y eso puede tener un impacto en el rendimiento, sobre todo cuando usamos estas cosas en dashboards, que son queries que se ejecutan muchas veces por segundo.

# Should es muy cabroncete...

ES UN MUTANTE, como los XMEN!

Si está solo, sin must, ni filter, se comporta de una forma.
    Al menos se debe cumplir un should para que el documento sea devuelto.

Pero si aparece en combinación con must o filter, se comporta de otra forma.
    Es una condición deseable, pero no obligatoria. Si se cumple, mejor para el score. Pero si no se cumple, no pasa nada.

La realidad es que lo que cambie entre usarlo solo o en combinación con must o filter, es el valor por defecto de minimum_should_match. 
    Si está solo, el valor por defecto es 1.
    Si está en combinación con must o filter, el valor por defecto es 0.

---

# Agregaciones

Sobre todo las usamos mucho en cuadros de mando.
Llevan a priori la misma sintaxis que las queries, solo añaden el campo "aggs"

    {
        "aggs": {
            "nombre_agregacion": {
                "tipo_agregacion": {
                    "field": "campo_a_agregar"
                }
            }
        }
    }


tipo_agregacion:
- terms -> Los valores de un campo contados: FREQUENCY
- avg -> Media de los valores de un campo
- min -> Valor mínimo de un campo
- max -> Valor máximo de un campo
- sum -> Suma de los valores de un campo
- stats -> Devuelve un objeto con min, max, avg, sum y count de un campo

---

Visualize:

    Me permite crear una representación de unos datos:
        - En forma de tabla
        - En forma de gráfico de barras
        - En forma de gráfico de líneas
        - En forma de gráfico de tarta
        - Como un mapa, si tengo datos de geolocalización
        - Mapas térmicos
        - Indicadores de KPI
  
Bashboards:
    Un dashboard es una colección de visualizaciones, que se pueden organizar en un panel de control.