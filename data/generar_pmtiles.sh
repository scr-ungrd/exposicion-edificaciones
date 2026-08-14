#!/bin/bash
# Regenera data/edificios.pmtiles a partir del shapefile fuente.
# Uso: bash data/generar_pmtiles.sh
set -euo pipefail

SHP="../../Edificios_GEE_Shp/Buildings.shp"
cd "$(dirname "$0")"

ogr2ogr -f GeoJSONSeq -lco COORDINATE_PRECISION=6 -select area_m2,confiab edificios.geojsonl "$SHP"

# maxzoom fijo en 13 (no -zg / --extend-zooms-if-still-dropping) para que el archivo
# quede bajo 100 MB y pueda commitearse directo al repo, sin necesitar hosting externo.
# Con -zg el auto-guess extendía a zoom 15 por la densidad de edificios -> 410 MB.
tippecanoe -o edificios.pmtiles -l edificios \
  -Z0 -z13 --drop-densest-as-needed --coalesce-densest-as-needed \
  -f edificios.geojsonl

rm edificios.geojsonl
echo "Listo: data/edificios.pmtiles"
