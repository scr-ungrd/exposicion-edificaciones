"""
Agrega los 6M polígonos de Buildings.shp (Google Open Buildings vía GEE) a una
grilla regular y genera un mapa estático (PNG) de densidad de edificaciones,
para insertar en 02-mapa-exposicion.qmd.

Lee el shapefile en streaming (batches de Arrow) para no cargar 6M geometrías
en memoria a la vez -- la máquina tiene 8 GB de RAM.
"""
import time

import numpy as np
import pyarrow as pa
import pyogrio
import shapely
from pyproj import Transformer

SHP = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/Edificios_GEE_Shp/Buildings.shp"
CELL_M = 2000  # tamaño de celda de la grilla, en metros
CRS_PROYECTADA = "EPSG:9377"  # MAGNA-SIRGAS-CTM12 Colombia (oficial IGAC)

# Extent conocido del shapefile (de ogrinfo), en WGS84 lon/lat
BBOX_WGS84 = (-77.864939, 2.348667, -73.642206, 7.718873)

transformer = Transformer.from_crs("EPSG:4326", CRS_PROYECTADA, always_xy=True)

# Límites de la grilla en la CRS proyectada, a partir de las esquinas del bbox
xs, ys = transformer.transform(
    [BBOX_WGS84[0], BBOX_WGS84[2], BBOX_WGS84[0], BBOX_WGS84[2]],
    [BBOX_WGS84[1], BBOX_WGS84[1], BBOX_WGS84[3], BBOX_WGS84[3]],
)
x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)

n_cols = int(np.ceil((x_max - x_min) / CELL_M)) + 1
n_rows = int(np.ceil((y_max - y_min) / CELL_M)) + 1
print(f"Grilla: {n_rows} filas x {n_cols} columnas (celda {CELL_M} m)")

count_grid = np.zeros((n_rows, n_cols), dtype=np.int64)
area_grid = np.zeros((n_rows, n_cols), dtype=np.float64)

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
        lon = shapely.get_x(centroids)
        lat = shapely.get_y(centroids)

        x_proj, y_proj = transformer.transform(lon, lat)

        col_idx = np.floor((x_proj - x_min) / CELL_M).astype(np.int64)
        row_idx = np.floor((y_proj - y_min) / CELL_M).astype(np.int64)
        np.clip(col_idx, 0, n_cols - 1, out=col_idx)
        np.clip(row_idx, 0, n_rows - 1, out=row_idx)

        np.add.at(count_grid, (row_idx, col_idx), 1)
        np.add.at(area_grid, (row_idx, col_idx), area)

        n_total += len(geoms)
        print(f"  {n_total:,} edificios procesados ({time.time() - t0:.0f}s)", end="\r")

print(f"\nListo: {n_total:,} edificios en {time.time() - t0:.0f}s")

np.savez(
    "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/exposicion-edificaciones/data/grilla_exposicion.npz",
    count_grid=count_grid,
    area_grid=area_grid,
    x_min=x_min,
    x_max=x_max,
    y_min=y_min,
    y_max=y_max,
    cell_m=CELL_M,
    crs=CRS_PROYECTADA,
)
print("Grilla guardada en data/grilla_exposicion.npz")
