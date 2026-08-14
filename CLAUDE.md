# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

Libro digital Quarto (`project: type: book`) en español: **"Exposición de edificaciones en Colombia"**, producido por la Subdirección de Conocimiento del Riesgo (SCR) de la UNGRD. Estructura y estilos calcados de `../../conociendo-el-riesgo-aguas-escorrentia` (ver su `CLAUDE.md` para las convenciones de estilo compartidas: clases `.ungrd-*` en `custom.css`, paleta institucional, `caption-bold.html`).

Repo: `github.com/scr-ungrd/exposicion-edificaciones`, publicado en `https://scr-ungrd.github.io/exposicion-edificaciones/` vía `.github/workflows/publish.yml` (igual que el resto de libros SCR).

## Historial: cómo se llegó a esta arquitectura

Punto de partida: un shapefile de edificaciones de Google Open Buildings (vía GEE) en `../Edificios_GEE_Shp/Buildings.shp` — 1.1 GB, 6.038.048 polígonos. No se puede desplegar tal cual en un libro/sitio Quarto (ni el navegador ni GitHub lo aguantan). Se evaluaron tres formas de representarlo:

- **(A) Mapa interactivo** — vector tiles (PMTiles) + MapLibre GL, huellas de edificación individuales, zoom libre.
- **(B) Imagen estática agregada** — polígonos agregados a una grilla regular, un PNG.
- **(C) Solo publicar el dataset referenciado** (p. ej. Zenodo, sin visualizarlo en el libro) — **descartada** por decisión explícita, no se implementó.

Se implementaron **A y B como complementarias**, no alternativas: B (`data/agregar_exposicion.py` + `graficar_mapa.py` → PNG) da una vista rápida de densidad a nivel país; A (`data/generar_pmtiles.sh` + el bloque MapLibre en `02-mapa-exposicion.qmd`) permite inspeccionar edificios uno por uno. A se desarrolló primero como proyecto Quarto separado (para no comprometer la estructura del libro mientras se resolvía el problema de tamaño) y luego se consolidó dentro del libro una vez validado.

**El problema central fue el tamaño del `.pmtiles`.** Con los parámetros por defecto de tippecanoe (`-zg --extend-zooms-if-still-dropping`, que deja que el algoritmo decida el zoom máximo) el archivo terminaba en maxzoom 15 y pesaba **410 MB** — muy por encima del límite de 100 MB de GitHub para un archivo en un commit normal. Antes de resolverlo se investigaron —y se descartaron, con evidencia— las alternativas nativas de GitHub para archivos grandes:

| Alternativa | Resultado | Cómo se verificó |
|---|---|---|
| Commit normal | Bloqueado, límite duro 100 MiB | Documentación oficial de GitHub (`about-large-files-on-github`) |
| Git LFS | Soportaría el tamaño (hasta 2 GB), pero **GitHub Pages no sirve archivos LFS** | Documentación oficial de GitHub, confirmado por búsqueda |
| GitHub Releases | Soporta HTTP Range Requests (`206 Partial Content`, backend Azure Blob)... | Probado con `curl` contra un asset real de un repo público (`git-lfs/git-lfs`) |
| GitHub Releases (cont.) | ...pero **no envía cabeceras CORS** (`Access-Control-Allow-Origin` ausente), así que el `fetch()` de PMTiles.js falla igual desde `scr-ungrd.github.io` | Mismo `curl`, con header `Origin` |
| GitHub for Nonprofits (LFS ampliado a 250 GB) | No aplica: el programa excluye explícitamente entidades **gubernamentales** (UNGRD lo es) | Documentación oficial de GitHub for Nonprofits |
| Compresión genérica (gzip sobre el `.pmtiles`) | Inútil: tippecanoe ya comprime cada tile con gzip internamente (una muestra de 2 MB solo bajó 0.7% al re-comprimirla) | Prueba directa con `gzip -9` sobre una muestra |

Con las rutas nativas de GitHub agotadas, la alternativa que se iba a implementar era un bucket externo (Google Cloud Storage, con Range Requests + CORS habilitados) apuntando `pmtilesUrl` allá. **Antes de montar esa infraestructura**, se probó reducir el archivo en origen:

1. Filtrar por confianza de detección (`confiab`) se descartó como palanca principal: `confiab>=0.75` solo baja a 4.54M edificios (75% del total), `confiab>=0.8` a 2.77M (46%) — insuficiente por sí solo para una reducción de ~4×.
2. **Bajar el zoom máximo fue la palanca correcta.** Se fijó `-Z0 -z13` (sin `-zg`/`--extend-zooms-if-still-dropping`) en vez de dejar que se extendiera a 15. Resultado: **37.7 MB** — sin necesidad de tocar el filtro de confianza.
3. Hallazgo no obvio durante la prueba: el tamaño del archivo **durante** la fase de tiling (visible con `ls -la` mientras corre) no es representativo del tamaño final — llegó a mostrar 128 MB al 99.4% de avance en zoom 13, y terminó en 37.7 MB tras la fase de compactación final de tippecanoe. No juzgar el resultado por el tamaño intermedio.
4. Se verificó visualmente (zoom hasta ~18, muy por encima del maxzoom real de 13) que el navegador hace *overzoom* de los tiles de zoom 13 sin pérdida perceptible de nitidez en los polígonos de edificios individuales — el recorte de zoom no tiene costo visual apreciable para este dataset.

Resultado: `data/edificios.pmtiles` (37.7 MB) sí está en git (excepción en `.gitignore`, ver abajo) y el mapa interactivo funciona directo en el sitio publicado, sin infraestructura externa.

## Datos fuente

Los datos crudos de edificaciones (huellas de Google Open Buildings vía GEE, shapefile de ~1.1 GB / 6M polígonos) viven en `../Edificios_GEE_Shp/` (un nivel arriba, fuera de este proyecto Quarto — no se copian aquí por su tamaño). A partir de ahí, el capítulo `02-mapa-exposicion.qmd` incluye dos mapas:

1. **Mapa estático agregado** (imagen): polígonos agregados a una grilla de 2×2 km (conteo por celda), generada con `data/agregar_exposicion.py` + `data/graficar_mapa.py` → `media/02-mapa-exposicion/densidad_edificaciones.png`.
2. **Mapa interactivo** (MapLibre GL + PMTiles): huellas de edificación individuales, vector tiles generados con `data/generar_pmtiles.sh` (usa `ogr2ogr` + `tippecanoe`) → `data/edificios.pmtiles`. Librerías locales (sin CDN) en `libs/` (`maplibre-gl.js/css`, `pmtiles.js`) — **`libs/` sí está en git** (a diferencia de `data/`), porque el capítulo las necesita en producción.

Los scripts (`*.py`, `*.sh`) y `data/edificios.pmtiles` **sí están en git** (excepciones explícitas en `.gitignore`, con `data/*` como regla base). Las salidas intermedias regenerables (`data/grilla_exposicion.npz`) siguen ignoradas.

**Dependencias a tener en cuenta si se reutilizan estos scripts:**
- `agregar_exposicion.py` tiene hardcodeado `BBOX_WGS84` (extent del shapefile actual, obtenido con `ogrinfo`) y rutas absolutas — para un dataset/región nueva hay que recalcular el bbox y actualizar las rutas.
- `graficar_mapa.py` depende de `MR-Web/datascience/mapas/data/col_departamentos.geojson` (**fuera de este repo**, otro proyecto) solo para dibujar el contorno de departamentos como contexto — si ese proyecto se mueve o no existe en la máquina, este script falla.

### Cómo repetir este proceso con un dataset nuevo (shapefile grande de polígonos)

1. `data/agregar_exposicion.py` (editar `SHP`, `BBOX_WGS84` vía `ogrinfo -al -so`) → `graficar_mapa.py` para el mapa estático agregado.
2. `data/generar_pmtiles.sh` (editar `SHP`) para el mapa interactivo. Primero probar con `-zg --extend-zooms-if-still-dropping` (deja que tippecanoe decida el zoom) — si el `.pmtiles` resultante pesa menos de ~50-80 MB, probablemente sirve tal cual.
3. Si supera ~90-100 MB: **antes de pensar en hosting externo**, fijar un maxzoom explícito más bajo (`-Z0 -zN` sin `-zg`/`--extend-zooms-if-still-dropping`) y volver a generar. Empezar en N=13; si sigue pesando de más, bajar a 12, 11... Solo recurrir a filtrar por atributos de confianza si bajar el zoom no alcanza (para este dataset, bajar a z13 solo, sin filtrar, ya resolvió el tamaño).
4. **No juzgar el tamaño mientras tippecanoe corre** — el archivo intermedio durante la fase de tiling puede verse 3× más grande que el resultado final compactado (ver ejemplo real en la sección de Historial arriba).
5. Verificar visualmente antes de dar por bueno el recorte de zoom: `npx serve` + zoom hasta el máximo del mapa (más allá del maxzoom real, para probar el *overzoom* del navegador) y confirmar que los polígonos individuales se sigan viendo nítidos.
6. Confirmar que `data/*.pmtiles` (o el nombre que uses) queda excluido de la regla general `data/*` en `.gitignore` con un `!data/tu-archivo.pmtiles`, y que los scripts (`*.py`/`*.sh`) también quedan versionados — si no, la próxima persona (o vos mismo) no podrá reproducir el proceso desde un clon limpio.
7. Agregar el `.pmtiles` a `project.resources` en `_quarto.yml` — sin esto, Quarto no lo copia a `_book/` (ni local ni en CI) porque solo se referencia desde JS, no desde un link/img estático. El síntoma es engañoso: todo renderiza sin error y la Action de despliegue queda en verde, pero el mapa no carga ningún edificio.
8. **Después de desplegar, verificar con `curl -I https://.../data/tu-archivo.pmtiles` que responda `200`, no `404`.** Un despliegue exitoso (Action en verde) no significa que el `.pmtiles` haya llegado al sitio — hay que comprobarlo aparte.

### `data/edificios.pmtiles` (37.7 MB) — sí está en git, no necesita hosting externo

Con los parámetros por defecto de tippecanoe (`-zg --extend-zooms-if-still-dropping`), el archivo se extendía a maxzoom 15 y pesaba 410 MB — superaba el límite de 100 MB de GitHub, y ni Git LFS (GitHub Pages no sirve archivos LFS) ni GitHub Releases (soporta Range Requests pero no envía cabeceras CORS, verificado empíricamente) servían como alternativa. La solución fue fijar `-Z0 -z13` en `data/generar_pmtiles.sh` (maxzoom fijo en 13, sin extender): el archivo baja a 37.7 MB — el navegador hace overzoom más allá de 13 sin pérdida perceptible de nitidez en los polígonos individuales (verificado visualmente hasta zoom 18). Filtrar por `confiab` no fue necesario (bajar el zoom fue suficiente).

Regenerar con `bash data/generar_pmtiles.sh` — toma ~15 min en esta máquina (8 GB RAM), la mayor parte en la fase de tiling de zoom 13.

### Preview local del mapa interactivo — usar `npx serve`, no `quarto preview`

El servidor de `quarto preview` no soporta HTTP Range Requests (responde `200` completo en vez de `206` parcial), que es lo que PMTiles necesita. Con `quarto preview` el mapa se queda cargando para siempre. Usar en su lugar:

```bash
quarto render      # genera _book/, incluyendo data/edificios.pmtiles (ver nota resources: abajo)
npx serve _book     # sirve con soporte real de Range Requests
```

**`resources:` en `_quarto.yml` es obligatorio para que esto funcione, tanto local como en la Action de CI.** Quarto no detecta automáticamente `data/edificios.pmtiles` como recurso a copiar a `_book/` porque solo se referencia desde una URL armada en JS (`fetch` de PMTiles.js dentro de un `<script>`), no como un link/img estático que Quarto pueda rastrear. Sin la entrada `resources: [data/edificios.pmtiles]` en `_quarto.yml`, el render "funciona" (no da error) pero el archivo simplemente no llega a `_book/data/` — **y esto se detectó tarde, después de dar por bueno el despliegue**: la Action corría en verde y el sitio se veía bien en general, pero el `.pmtiles` devolvía 404 y el mapa interactivo no cargaba ningún edificio al hacer zoom. Verificar siempre con `curl -I https://scr-ungrd.github.io/exposicion-edificaciones/data/edificios.pmtiles` (debe dar `200`, no `404`) después de cualquier cambio a `_quarto.yml`, `.gitignore` o el pipeline de generación del `.pmtiles` — un workflow en verde no garantiza que los recursos estáticos referenciados solo desde JS hayan llegado al sitio.

## Comandos

```bash
quarto preview          # servidor local con recarga en vivo al editar .qmd/.css
quarto render           # compila el sitio HTML estático a _book/
quarto render --to pdf  # compila la versión PDF (requiere motor LaTeX, p.ej. TinyTeX)
```

## Pendientes conocidos (marcados como TODO en los .qmd)

- Portada propia (actualmente usa el logo genérico UNGRD en vez de un cubo/portada dedicada).
- Texto de `presentacion.qmd`.
- DOI y metadatos definitivos en `Pagina-legal.qmd` (actualmente placeholders `PENDIENTE`).
- El dataset cubre el corredor andino suroccidental de Colombia, no la totalidad del territorio nacional — ajustar alcance/título si se espera cobertura nacional.

## Estructura y orden de capítulos

El orden y la lista de capítulos viven en `_quarto.yml` (`book.chapters`):

```
index.qmd → Pagina-legal.qmd → presentacion.qmd → 01-metodologia.qmd →
02-mapa-exposicion.qmd → 03-referencias-bibliograficas.qmd
```
