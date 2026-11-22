# NutriAndes · Tablero comercial multicanal (PMV)

Dashboard interactivo en **Python + Streamlit + Plotly** para analizar las ventas
de una tienda de suplementos nutricionales por canal, producto y ciudad.

> **Datos ficticios.** NutriAndes S.A.S. es una empresa inventada. Los datos se
> generan con `generar_datos.py` (simulación con semilla fija) y no corresponden
> a ninguna empresa real.

Proyecto académico · Visualización de Datos · Institución Universitaria
Politécnico Grancolombiano.

## Qué incluye

- **KPIs**: ventas netas, margen bruto, pedidos, ticket promedio, tasa de
  devolución y calificación del cliente, comparados con el mismo periodo del
  año anterior.
- **Filtros dinámicos**: periodo (fechas), canal, categoría y ciudad.
- **Hallazgos automáticos** (storytelling) que cambian con los filtros.
- **Pestañas**: tendencias, productos y ciudades, distribución, correlaciones y
  datos (con descarga en CSV).

## Estructura

```
app.py              # la aplicación
generar_datos.py    # genera los datos ficticios
data/ventas.csv     # 19.399 pedidos (ene 2025 – oct 2026)
data/marketing.csv  # inversión publicitaria mensual por canal
requirements.txt
.streamlit/config.toml
```

## Ejecutar en el computador

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar gratis en Streamlit Community Cloud

1. Crear un repositorio público en GitHub y subir **todos** estos archivos
   (incluida la carpeta `data` y `.streamlit`).
2. Entrar a <https://share.streamlit.io> con la cuenta de GitHub.
3. **Create app → Deploy a public app from GitHub**, elegir el repositorio,
   rama `main` y archivo principal `app.py`.
4. Clic en **Deploy**. En 2-3 minutos queda una URL pública
   (`https://<nombre>.streamlit.app`).
