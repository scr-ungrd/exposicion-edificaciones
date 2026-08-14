# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

Libro digital Quarto (`project: type: book`) en español: **"Exposición de edificaciones en Colombia"**, producido por la Subdirección de Conocimiento del Riesgo (SCR) de la UNGRD. Estructura y estilos calcados de `../../conociendo-el-riesgo-aguas-escorrentia` (ver su `CLAUDE.md` para las convenciones de estilo compartidas: clases `.ungrd-*` en `custom.css`, paleta institucional, `caption-bold.html`).

Este proyecto todavía no tiene repo en GitHub ni publicación en GitHub Pages (a diferencia del resto de libros SCR) — se decidió mantenerlo solo local hasta que el contenido esté listo.

## Datos fuente

Los datos crudos de edificaciones (huellas de Google Open Buildings vía GEE, shapefile de ~1.1 GB / 6M polígonos) viven en `../Edificios_GEE_Shp/` (un nivel arriba, fuera de este proyecto Quarto — no se copian aquí por su tamaño). El plan es:

1. Agregar los polígonos a una grilla/hexágonos (conteo y/o área construida por celda) — ver `02-metodologia.qmd`.
2. Exportar el resultado como imagen estática (PNG) a `media/03-mapa-exposicion/`.
3. Referenciar esa imagen desde `03-mapa-exposicion.qmd`.

Los scripts de procesamiento y salidas intermedias deben ir en `data/` (ya está en `.gitignore`, siguiendo la misma convención que el resto de libros SCR).

## Comandos

```bash
quarto preview          # servidor local con recarga en vivo al editar .qmd/.css
quarto render           # compila el sitio HTML estático a _book/
quarto render --to pdf  # compila la versión PDF (requiere motor LaTeX, p.ej. TinyTeX)
```

## Pendientes conocidos (marcados como TODO en los .qmd)

- Portada propia (actualmente usa el logo genérico UNGRD en vez de un cubo/portada dedicada).
- Texto de `01-presentacion.qmd`.
- DOI y metadatos definitivos en `Pagina-legal.qmd` (actualmente placeholders `PENDIENTE`).
- Generar y enlazar el mapa agregado en `03-mapa-exposicion.qmd`.
- Decidir cuándo crear el repo `scr-ungrd/exposicion-edificaciones` en GitHub y activar el workflow de auto-publish (copiar `.github/workflows/publish.yml` del libro plantilla cuando corresponda).

## Estructura y orden de capítulos

El orden y la lista de capítulos viven en `_quarto.yml` (`book.chapters`):

```
index.qmd → Pagina-legal.qmd → 01-presentacion.qmd → 02-metodologia.qmd →
03-mapa-exposicion.qmd → 04-referencias-bibliograficas.qmd
```
