"""
Genera el PNG del mapa de densidad de edificaciones a partir de
data/grilla_exposicion.npz (producida por agregar_exposicion.py).

Paleta secuencial de un solo tono (azul institucional UNGRD #223764),
claro -> oscuro, con escala logarítmica dado lo sesgado de la densidad
(mediana 32 vs máximo ~25,000 edificios/celda).
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm

DATA = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/exposicion-edificaciones/data/grilla_exposicion.npz"
DEPARTAMENTOS = "/Users/mauricio/Documents/Data-science-local/MR-Web/datascience/mapas/data/col_departamentos.geojson"
OUT_PNG = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/exposicion-edificaciones/media/02-mapa-exposicion/densidad_edificaciones.png"

d = np.load(DATA)
count_grid = d["count_grid"].astype(float)
x_min, x_max = float(d["x_min"]), float(d["x_max"])
y_min, y_max = float(d["y_min"]), float(d["y_max"])
crs = str(d["crs"])

count_grid[count_grid == 0] = np.nan

# Rampa secuencial de un solo tono: tinte claro -> azul UNGRD oscuro (#223764)
cmap = LinearSegmentedColormap.from_list(
    "ungrd_azul_secuencial", ["#eef2f8", "#7f97bb", "#223764"]
)
cmap.set_bad(color="#f7f8fa", alpha=0)  # celdas sin edificios: transparente

deptos = gpd.read_file(DEPARTAMENTOS).to_crs(crs)

fig, ax = plt.subplots(figsize=(8, 9.5), dpi=300)

deptos.plot(ax=ax, color="#eef0f2", edgecolor="none", zorder=0)
deptos.boundary.plot(ax=ax, linewidth=0.4, color="#9aa5b1", zorder=1)

im = ax.imshow(
    count_grid,
    origin="lower",
    extent=(x_min, x_max, y_min, y_max),
    cmap=cmap,
    norm=LogNorm(vmin=1, vmax=np.nanmax(count_grid)),
    zorder=2,
)

deptos.boundary.plot(ax=ax, linewidth=0.4, color="#5a6472", zorder=3)

# Se muestra el país completo como contexto (los datos solo cubren una subregión)
co_x_min, co_y_min, co_x_max, co_y_max = deptos.total_bounds
ax.set_xlim(co_x_min, co_x_max)
ax.set_ylim(co_y_min, co_y_max)
ax.set_aspect("equal")
ax.set_axis_off()

cbar = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.04, pad=0.02)
cbar.set_label("Edificios por celda de 2 × 2 km (escala log)", fontsize=9)
cbar.ax.tick_params(labelsize=8)

fig.tight_layout()
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
print(f"Guardado: {OUT_PNG}")
