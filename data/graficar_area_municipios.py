"""
Genera el mapa coroplético de área construida por municipio a partir de
data/area_por_municipio.csv (producido por agregar_por_municipio.py).

Mismo estilo que graficar_mapa.py: rampa secuencial de un solo tono
(azul institucional UNGRD), escala logarítmica por lo sesgada que es
la distribución (mediana 0.52 km2 vs máximo 114.45 km2 en Bogotá D.C.).
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm

MUNICIPIOS = "/Users/mauricio/Documents/Data-science-local/MR-Web/datascience/mapas/data/col_municipios.geojson"
DEPARTAMENTOS = "/Users/mauricio/Documents/Data-science-local/MR-Web/datascience/mapas/data/col_departamentos.geojson"
CSV = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/exposicion-edificaciones/data/area_por_municipio.csv"
OUT_PNG = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/exposicion-edificaciones/media/02-mapa-exposicion/area_por_municipio.png"

area = pd.read_csv(CSV)
muni = gpd.read_file(MUNICIPIOS)
muni = muni.merge(area[["departamento", "municipio", "area_construida_km2"]],
                   on=["departamento", "municipio"], how="left")

deptos = gpd.read_file(DEPARTAMENTOS)

cmap = LinearSegmentedColormap.from_list(
    "ungrd_azul_secuencial", ["#eef2f8", "#7f97bb", "#223764"]
)
cmap.set_bad(color="#f7f8fa", alpha=0)

fig, ax = plt.subplots(figsize=(7, 10), dpi=300)

deptos.plot(ax=ax, color="#eef0f2", edgecolor="none", zorder=0)

muni.plot(
    ax=ax,
    column="area_construida_km2",
    cmap=cmap,
    norm=LogNorm(vmin=area["area_construida_km2"].min(), vmax=area["area_construida_km2"].max()),
    edgecolor="none",
    missing_kwds={"color": "none"},
    zorder=1,
)

deptos.boundary.plot(ax=ax, linewidth=0.4, color="#9aa5b1", zorder=2)

co_x_min, co_y_min, co_x_max, co_y_max = deptos.total_bounds
ax.set_xlim(co_x_min, co_x_max)
ax.set_ylim(co_y_min, co_y_max)
ax.set_aspect("equal")
ax.set_axis_off()

sm = plt.cm.ScalarMappable(
    cmap=cmap,
    norm=LogNorm(vmin=area["area_construida_km2"].min(), vmax=area["area_construida_km2"].max()),
)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04, pad=0.02)
cbar.set_label("Área construida por municipio (km², escala log)", fontsize=9)
cbar.ax.tick_params(labelsize=8)

fig.tight_layout()
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
print(f"Guardado: {OUT_PNG}")
