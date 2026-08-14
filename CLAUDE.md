# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

Libro digital Quarto (`project: type: book`) en español: **"Exposición de edificaciones en Colombia"**, producido por la Subdirección de Conocimiento del Riesgo (SCR) de la UNGRD. Estructura y estilos calcados de `../../conociendo-el-riesgo-aguas-escorrentia` (ver su `CLAUDE.md` para las convenciones de estilo compartidas: clases `.ungrd-*` en `custom.css`, paleta institucional, `caption-bold.html`).

Repo: `github.com/scr-ungrd/exposicion-edificaciones`, publicado en `https://scr-ungrd.github.io/exposicion-edificaciones/` vía `.github/workflows/publish.yml` (igual que el resto de libros SCR).

## Datos fuente

Los datos crudos de edificaciones (huellas de Google Open Buildings vía GEE, shapefile de ~1.1 GB / 6M polígonos) viven en `../Edificios_GEE_Shp/` (un nivel arriba, fuera de este proyecto Quarto — no se copian aquí por su tamaño). A partir de ahí, el capítulo `02-mapa-exposicion.qmd` incluye dos mapas:

1. **Mapa estático agregado** (imagen): polígonos agregados a una grilla de 2×2 km (conteo por celda), generada con `data/agregar_exposicion.py` + `data/graficar_mapa.py` → `media/02-mapa-exposicion/densidad_edificaciones.png`.
2. **Mapa interactivo** (MapLibre GL + PMTiles): huellas de edificación individuales, vector tiles generados con `data/generar_pmtiles.sh` (usa `ogr2ogr` + `tippecanoe`) → `data/edificios.pmtiles`. Librerías locales (sin CDN) en `libs/` (`maplibre-gl.js/css`, `pmtiles.js`) — **`libs/` sí está en git** (a diferencia de `data/`), porque el capítulo las necesita en producción.

Los scripts de procesamiento y salidas intermedias van en `data/` (en `.gitignore`, siguiendo la misma convención que el resto de libros SCR).

### `data/edificios.pmtiles` (410 MB) — no está en git, y por ahora el mapa interactivo no funciona en el sitio publicado

Este archivo supera el límite de 100 MB de GitHub y no puede resolverse con Git LFS (GitHub Pages no sirve archivos LFS — confirmado en la documentación oficial) ni con GitHub Releases (sí soporta Range Requests, pero no envía cabeceras CORS, así que el `fetch()` de PMTiles.js falla igual desde otro origen — verificado empíricamente). **Pendiente**: subir `edificios.pmtiles` a un bucket externo con Range Requests + CORS habilitados (p. ej. Google Cloud Storage) y apuntar `pmtilesUrl` en `02-mapa-exposicion.qmd` allá en vez de a `data/edificios.pmtiles` local. Hasta que eso se resuelva, el mapa interactivo solo funciona en preview local.

### Preview local del mapa interactivo — usar `npx serve`, no `quarto preview`

El servidor de `quarto preview` no soporta HTTP Range Requests (responde `200` completo en vez de `206` parcial), que es lo que PMTiles necesita. Con `quarto preview` el mapa se queda cargando para siempre. Usar en su lugar:

```bash
quarto render                                    # genera _book/
cp data/edificios.pmtiles _book/data/edificios.pmtiles  # el render no copia data/ (está en .gitignore)
npx serve _book                                  # sirve con soporte real de Range Requests
```

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
- Hospedar `data/edificios.pmtiles` externamente para que el mapa interactivo funcione en el sitio publicado (ver sección de datos arriba).
- El dataset cubre el corredor andino suroccidental de Colombia, no la totalidad del territorio nacional — ajustar alcance/título si se espera cobertura nacional.

## Estructura y orden de capítulos

El orden y la lista de capítulos viven en `_quarto.yml` (`book.chapters`):

```
index.qmd → Pagina-legal.qmd → presentacion.qmd → 01-metodologia.qmd →
02-mapa-exposicion.qmd → 03-referencias-bibliograficas.qmd
```
