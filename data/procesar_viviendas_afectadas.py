"""
Limpia el Excel de viviendas afectadas (Valle del Cauca) y normaliza los
nombres de municipio contra la fuente oficial (mismo origen GADM v4.1 que
col_municipios.geojson / colombia_moderate.topojson), para poder unirlo
con el topojson en el mapa D3 del capítulo 03-viviendas-afectadas.qmd.

El Excel original no trae tildes en los nombres de municipio y tiene una
fila de nota al pie (Cod DIVIPOLA) que se descarta. No incluye Santiago de
Cali (ausente del archivo fuente, no es un error de este script).
"""
import re
import unicodedata

import pandas as pd

XLSX = "/Users/mauricio/Downloads/VIVIENDAS AFECTADAS ANALISIS.xlsx"
OUT_CSV = "/Users/mauricio/Documents/Data-science-local/A-SCR/Libros-SCR/exposicion/exposicion-edificaciones/data/viviendas_afectadas_valle.csv"

MUNICIPIOS_VALLE = [
    "Alcalá", "Andalucía", "Ansermanuevo", "Argelia", "Bolívar", "Buenaventura",
    "Bugalagrande", "Caicedonia", "Calima", "Candelaria", "Cartago", "Dagua",
    "El Cairo", "El Cerrito", "El Dovio", "El Águila", "Florida", "Ginebra",
    "Guacarí", "Guadalajara de Buga", "Jamundí", "La Cumbre", "La Unión",
    "La Victoria", "Obando", "Palmira", "Pradera", "Restrepo", "Riofrío",
    "Roldanillo", "San Pedro", "Santiago de Cali", "Sevilla", "Toro",
    "Trujillo", "Tuluá", "Ulloa", "Versalles", "Vijes", "Yotoco", "Yumbo",
    "Zarzal",
]


def normalizar(s):
    s = str(s).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


oficial_por_norm = {normalizar(m): m for m in MUNICIPIOS_VALLE}

df = pd.read_excel(XLSX)
df = df[df["MUNICIPIO"] != "Municipio"].copy()  # descarta la fila de nota al pie

df["norm"] = df["MUNICIPIO"].apply(normalizar)
df.loc[df["MUNICIPIO"].str.contains("Calima", case=False, na=False), "norm"] = "calima"
df["municipio"] = df["norm"].map(oficial_por_norm)

sin_match = df[df["municipio"].isna()]
if len(sin_match):
    raise SystemExit(f"Municipios sin coincidencia oficial: {sin_match['MUNICIPIO'].tolist()}")

df["departamento"] = "Valle del Cauca"
df = df.rename(columns={
    "VIVIENDA UNIFAMILIAR": "vivienda_unifamiliar",
    "VIVIENDA AFECTADA": "vivienda_afectada",
    "PORCENTAJE DE VIVIENDAS AFECTADAS": "porcentaje_afectadas",
})
df["porcentaje_afectadas_pct"] = df["porcentaje_afectadas"] * 100

out = df[["departamento", "municipio", "vivienda_unifamiliar", "vivienda_afectada",
          "porcentaje_afectadas", "porcentaje_afectadas_pct"]].sort_values(
    "porcentaje_afectadas", ascending=False
)
out.to_csv(OUT_CSV, index=False)
print(f"Guardado: {OUT_CSV} ({len(out)} municipios)")
print(out.to_string(index=False))
