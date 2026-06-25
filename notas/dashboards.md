
Vamos de lo más general a lo más específico.
No hacemos 1 solo dashboard... hago varios.. Entrando en detalle.


Streaming Operations Overview: visión operativa de un vistazo. Es el dashboard "de pantalla grande" del NOC.

    EVENTOS DE STREAMING

    RECUENTO EVENTOS

      "latency_ms":       { "type": "integer" },
            MEDIA
            P95
      "duration_ms":      { "type": "integer" },
            MEDIA
            P95
      "bytes_sent":       { "type": "long" },
            SUMA

      "bitrate_kbps":     { "type": "integer" },
            MEDIA
            P95

      "cache_hit":        { "type": "boolean" },
        RATIO DE CACHE HIT % <- FRECUENCIA!
      "is_error":         { "type": "boolean" },
        RATIO DE ERROR % <- FRECUENCIA!

    --- Podemos complementarlo con algunos básicos de KEYWORDS (NOMINALES|ORDINALES) de muy baja cardinalidad

      "level":            { "type": "keyword" },
            INFO   
            WARNING   
            ERROR

        "service":          { "type": "keyword" },
            player-api
            cdn-edge
            cdn-origin
            cdn-analytics
        tipo de evento: "event_type":       { "type": "keyword" },
            playback-start
            playback-stop
            playback-error
            playback-buffering
            playback-rebuffering
            playback-seek
            playback-quality-change
            playback-ad-start
            playback-ad-end
            playback-ad-error


    EVENTOS DE STREAMING por ZONAS

    CONTENIDOS QUE SE VISUALIZAN

    PERFIL DE LOS CLIENTES

    DETALLE DE ERRORES

    CALIDAD DE SERVICIO

    SALUD DE SERVICIOS
