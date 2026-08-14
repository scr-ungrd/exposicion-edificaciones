"""
Agrega los 6M polígonos de Buildings.shp por municipio (área construida total
y conteo de edificios), vía join espacial del centroide de cada edificio contra
los límites municipales de Colombia.

Lee el shapefile en streaming (batches de Arrow) igual que agregar_exposicion.py.
"""
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyogrio
import shapely
from shapely import STRtree

SHP = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/Edificios_GEE_Shp/Buildings.shp"
MUNICIPIOS = "/Users/mauricio/Documents/Data-science-local/MR-Web/datascience/mapas/data/col_municipios.geojson"
OUT_CSV = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/exposicion-edificaciones/data/area_por_municipio.csv"

muni = gpd.read_file(MUNICIPIOS)
tree = STRtree(muni.geometry.values)
n_muni = len(muni)
print(f"{n_muni} municipios cargados")

area_sum = np.zeros(n_muni, dtype=np.float64)
count_sum = np.zeros(n_muni, dtype=np.int64)
sin_municipio_area = 0.0
sin_municipio_n = 0

t0 = time.time()
n_total = 0

with pyogrio.open_arrow(
    SHP,
    columns=["area_m2"],
    batch_size=200_000,
    use_pyarrow=True,
) as (meta, reader):
    geom_col = meta["geometry_name"] or "wkb_geometry"
    for batch in reader:
        tbl = pa.Table.from_batches([batch])
        wkb = tbl.column(geom_col).to_numpy(zero_copy_only=False)
        area = tbl.column("area_m2").to_numpy(zero_copy_only=False)

        geoms = shapely.from_wkb(wkb)
        centroids = shapely.centroid(geoms)

        input_idx, muni_idx = tree.query(centroids, predicate="within")

        np.add.at(area_sum, muni_idx, area[input_idx])
        np.add.at(count_sum, muni_idx, 1)

        matched = len(input_idx)
        sin_municipio_n += len(centroids) - matched
        if matched < len(centroids):
            unmatched_mask = np.ones(len(centroids), dtype=bool)
            unmatched_mask[input_idx] = False
            sin_municipio_area += area[unmatched_mask].sum()

        n_total += len(geoms)
        print(f"  {n_total:,} edificios procesados ({time.time() - t0:.0f}s)", end="\r")

print(f"\nListo: {n_total:,} edificios en {time.time() - t0:.0f}s")
print(f"Sin municipio asignado (fuera de límites o en el mar): {sin_municipio_n:,} edificios, "
      f"{sin_municipio_area/1e6:.2f} km2")

out = pd.DataFrame({
    "departamento": muni["departamento"].values,
    "municipio": muni["municipio"].values,
    "n_edificios": count_sum.astype(int),
    "area_construida_km2": area_sum / 1e6,
})
out = out[out["n_edificios"] > 0].sort_values("area_construida_km2", ascending=False)
out.to_csv(OUT_CSV, index=False)
print(f"Guardado: {OUT_CSV} ({len(out)} municipios con datos)")
print(out.head(20).to_string(index=False))
