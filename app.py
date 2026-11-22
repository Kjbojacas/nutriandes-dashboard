"""NutriAndes · Tablero comercial multicanal (PMV)

Dashboard interactivo en Streamlit sobre datos FICTICIOS de ventas de una
tienda de suplementos nutricionales inventada (NutriAndes S.A.S.).
Ejecutar localmente con:  streamlit run app.py
"""
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Configuración general y estilo
# ----------------------------------------------------------------------------
st.set_page_config(page_title="NutriAndes · Tablero comercial",
                   page_icon="📊", layout="wide")

DATA = Path(__file__).parent / "data"

# Color fijo por canal (sigue a la entidad, no a su posición en el ranking)
COLOR_CANAL = {
    "Ecommerce": "#2a78d6",
    "Mercado Libre": "#eb6834",
    "Mayorista": "#1baf7a",
    "Dropshipping": "#eda100",
    "Tiendas propias": "#e87ba4",
}
ORDEN_CANAL = list(COLOR_CANAL)
AZUL, GRIS, TINTA = "#2a78d6", "#52514e", "#0b0b0b"
MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
h1 {font-size: 1.75rem !important; margin-bottom: 0 !important;}
[data-testid="stMetricValue"] {font-size: 1.45rem;}
[data-testid="stMetricLabel"] p {font-size: 0.85rem; color: #52514e;}
div[data-testid="stMetric"] {background: #f6f6f4; border-radius: 10px;
    padding: 10px 14px; border: 1px solid #ecebe7;}
.insight {background: #eef4fc; border-left: 4px solid #2a78d6;
    border-radius: 6px; padding: 10px 14px; margin: 4px 0 10px 0;
    font-size: 0.95rem;}
.nota {color: #6b6a66; font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)


def cop(x: float, decimales: int = 0) -> str:
    """Formato de pesos colombianos: $1.234.567."""
    s = f"{x:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "$" + s


def num(x: float, dec: int = 1) -> str:
    """Número con coma decimal (formato colombiano)."""
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def millones(x: float) -> str:
    return f"${x / 1e6:,.1f} M".replace(",", "X").replace(".", ",").replace("X", ".")


def estilo(fig: go.Figure, alto: int = 380, leyenda: bool = True) -> go.Figure:
    """Estilo común: fondo limpio, grilla tenue, leyenda arriba."""
    fig.update_layout(
        template="plotly_white", height=alto, separators=",.",
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="Inter, Segoe UI, sans-serif", size=13, color=TINTA),
        title_font=dict(size=16),
        hoverlabel=dict(bgcolor="white", font_size=13),
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left",
                    x=0, title_text=""),
    )
    fig.update_xaxes(showgrid=False, linecolor="#d6d5d0")
    fig.update_yaxes(gridcolor="#ecebe7", zeroline=False)
    return fig


# ----------------------------------------------------------------------------
# Carga y preparación de datos
# ----------------------------------------------------------------------------
@st.cache_data
def cargar():
    v = pd.read_csv(DATA / "ventas.csv", parse_dates=["fecha"])
    v["margen"] = v["venta_neta"] - v["costo"]
    v["mes"] = v["fecha"].dt.to_period("M").dt.to_timestamp()
    m = pd.read_csv(DATA / "marketing.csv")
    m["mes"] = pd.to_datetime(m["mes"])
    return v, m


ventas, marketing = cargar()
f_min, f_max = ventas["fecha"].min().date(), ventas["fecha"].max().date()

# ----------------------------------------------------------------------------
# Encabezado y filtros (una sola fila sobre los gráficos)
# ----------------------------------------------------------------------------
st.title("NutriAndes · Tablero comercial multicanal")
st.markdown('<span class="nota">Ventas de suplementos nutricionales por canal, '
            'producto y ciudad · Datos ficticios generados para fines académicos</span>',
            unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([1.3, 1.4, 1.4, 1.2])
with c1:
    rango = st.date_input("Periodo", value=(date(2026, 1, 1), f_max),
                          min_value=f_min, max_value=f_max, format="DD/MM/YYYY")
with c2:
    canales_sel = st.multiselect("Canal de venta", ORDEN_CANAL,
                                 placeholder="Todos los canales")
with c3:
    categorias = sorted(ventas["categoria"].unique())
    cats_sel = st.multiselect("Categoría", categorias,
                              placeholder="Todas las categorías")
with c4:
    ciudades = sorted(ventas["ciudad"].unique())
    ciud_sel = st.multiselect("Ciudad", ciudades, placeholder="Todas las ciudades")

# El selector de fechas devuelve una sola fecha mientras el usuario elige el rango
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    ini, fin = rango
else:
    ini, fin = f_min, f_max

canales_f = canales_sel or ORDEN_CANAL
cats_f = cats_sel or categorias
ciud_f = ciud_sel or ciudades


def filtrar(df, desde, hasta):
    return df[(df["fecha"].dt.date >= desde) & (df["fecha"].dt.date <= hasta)
              & df["canal"].isin(canales_f) & df["categoria"].isin(cats_f)
              & df["ciudad"].isin(ciud_f)]


d = filtrar(ventas, ini, fin)
# Mismo periodo del año anterior, para comparar (evita el sesgo de estacionalidad)
def un_anio_antes(f):
    try:
        return f.replace(year=f.year - 1)
    except ValueError:  # 29 de febrero
        return f.replace(year=f.year - 1, day=28)


d_ant = filtrar(ventas, un_anio_antes(ini), un_anio_antes(fin))

if d.empty:
    st.warning("No hay pedidos con esa combinación de filtros. "
               "Amplía el periodo o quita algún filtro.")
    st.stop()

mk = marketing[(marketing["mes"].dt.date >= ini.replace(day=1))
               & (marketing["mes"].dt.date <= fin) & marketing["canal"].isin(canales_f)]

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
def kpis(df):
    if df.empty:
        return None
    vn = df["venta_neta"].sum()
    return dict(ventas=vn, margen=df["margen"].sum() / vn * 100,
                pedidos=len(df), ticket=vn / len(df),
                devol=df["devuelto"].mean() * 100,
                calif=df["calificacion"].mean())


k, ka = kpis(d), kpis(d_ant)


def delta(clave, pct=True, invertir=False):
    if ka is None:
        return None
    if pct:
        cambio = (k[clave] / ka[clave] - 1) * 100
        return f"{num(cambio, 1) if cambio < 0 else '+' + num(cambio, 1)}% vs. año anterior"
    cambio = k[clave] - ka[clave]
    dec = 2 if clave == "calif" else 1
    return f"{num(cambio, dec) if cambio < 0 else '+' + num(cambio, dec)} pts vs. año anterior"


cols = st.columns(6)
cols[0].metric("Ventas netas", millones(k["ventas"]), delta("ventas"))
cols[1].metric("Margen bruto", f"{num(k['margen'])}%", delta("margen", pct=False))
cols[2].metric("Pedidos", f"{k['pedidos']:,}".replace(",", "."), delta("pedidos"))
cols[3].metric("Ticket promedio", cop(k["ticket"]), delta("ticket"))
cols[4].metric("Tasa de devolución", f"{num(k['devol'])}%",
               delta("devol", pct=False), delta_color="inverse")
cols[5].metric("Calificación (1-5)", num(k['calif'], 2),
               delta("calif", pct=False))

# ----------------------------------------------------------------------------
# Storytelling: hallazgos calculados sobre la selección actual
# ----------------------------------------------------------------------------
por_canal = (d.groupby("canal")
             .agg(ventas=("venta_neta", "sum"), margen=("margen", "sum"),
                  pedidos=("id_pedido", "count"), devol=("devuelto", "mean"),
                  dias=("dias_entrega", "mean"), calif=("calificacion", "mean"))
             .reindex([c for c in ORDEN_CANAL if c in d["canal"].unique()]))
por_canal["participacion"] = por_canal["ventas"] / por_canal["ventas"].sum() * 100
por_canal["margen_pct"] = por_canal["margen"] / por_canal["ventas"] * 100

lider = por_canal["participacion"].idxmax()
peor_dev = por_canal["devol"].idxmax()
hallazgos = [f"<b>{lider}</b> es el canal que más vende: "
             f"{por_canal.loc[lider, 'participacion']:.0f}% de las ventas del periodo."]
if len(por_canal) > 1:
    hallazgos.append(
        f"<b>{peor_dev}</b> tiene la mayor tasa de devolución "
        f"({num(por_canal.loc[peor_dev, 'devol'] * 100)}%) y una calificación de "
        f"{num(por_canal.loc[peor_dev, 'calif'], 2)}: revisar tiempos de entrega "
        f"({num(por_canal.loc[peor_dev, 'dias'])} días en promedio).")
top_prod = d.groupby("producto")["margen"].sum().idxmax()
hallazgos.append(f"El producto que más margen deja es <b>{top_prod}</b>.")
st.markdown('<div class="insight">💡 ' + "<br>💡 ".join(hallazgos) + "</div>",
            unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Pestañas de análisis
# ----------------------------------------------------------------------------
t1, t2, t3, t4, t5 = st.tabs(["📈 Tendencias", "🏷️ Productos y ciudades",
                              "📊 Distribución", "🔗 Correlaciones",
                              "🗂️ Datos"])

# --- 1. Tendencias ------------------------------------------------------------
with t1:
    gran = st.radio("Ver por", ["Mes", "Semana"], horizontal=True,
                    label_visibility="collapsed")
    frec = "MS" if gran == "Mes" else "W-MON"
    serie = (d.set_index("fecha").groupby("canal")
             .resample(frec)["venta_neta"].sum().reset_index())
    serie["millones"] = serie["venta_neta"] / 1e6
    fig = px.line(serie, x="fecha", y="millones", color="canal",
                  color_discrete_map=COLOR_CANAL,
                  category_orders={"canal": ORDEN_CANAL},
                  labels={"fecha": "", "millones": "Ventas (millones COP)",
                          "canal": "Canal"},
                  title=f"Ventas netas por canal ({gran.lower()})")
    fig.update_traces(line=dict(width=2.2),
                      hovertemplate="%{x|%d/%m/%Y}<br>$%{y:,.1f} M<extra>%{fullData.name}</extra>")
    fig.update_layout(hovermode="x unified")
    meses_eje = pd.date_range(serie["fecha"].min().to_period("M").to_timestamp(),
                              serie["fecha"].max(), freq="MS")
    paso = 1 if len(meses_eje) <= 12 else 2
    fig.update_xaxes(tickvals=meses_eje[::paso],
                     ticktext=[f"{MESES[m.month - 1]} {m:%y}" for m in meses_eje[::paso]])
    st.plotly_chart(estilo(fig, 420), use_container_width=True)
    st.caption("Picos esperados en enero (propósitos de año nuevo) y noviembre "
               "(Black Friday). Mercado Libre es el canal que más crece.")

    a, b = st.columns(2)
    with a:
        pc = por_canal.reset_index().sort_values("ventas")
        fig = px.bar(pc, x="participacion", y="canal", orientation="h",
                     color="canal", color_discrete_map=COLOR_CANAL,
                     text=pc["participacion"].map(lambda x: f"{num(x)}%"),
                     labels={"participacion": "% de las ventas", "canal": ""},
                     title="Participación de cada canal en las ventas")
        fig.update_traces(textposition="outside", cliponaxis=False,
                          hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        fig.update_xaxes(range=[0, pc["participacion"].max() * 1.18])
        st.plotly_chart(estilo(fig, 340, leyenda=False), use_container_width=True)
    with b:
        pc = por_canal.reset_index().sort_values("margen_pct")
        fig = px.bar(pc, x="margen_pct", y="canal", orientation="h",
                     color="canal", color_discrete_map=COLOR_CANAL,
                     text=pc["margen_pct"].map(lambda x: f"{num(x)}%"),
                     labels={"margen_pct": "Margen bruto (%)", "canal": ""},
                     title="Margen bruto por canal")
        fig.update_traces(textposition="outside", cliponaxis=False,
                          hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        fig.update_xaxes(range=[0, pc["margen_pct"].max() * 1.18])
        st.plotly_chart(estilo(fig, 340, leyenda=False), use_container_width=True)

# --- 2. Productos y ciudades --------------------------------------------------
with t2:
    a, b = st.columns([1.25, 1])
    with a:
        metrica = st.segmented_control(
            "Ordenar productos por", ["Ventas", "Margen", "Unidades"],
            default="Ventas")
        col = {"Ventas": "venta_neta", "Margen": "margen",
               "Unidades": "unidades"}[metrica or "Ventas"]
        pr = (d.groupby(["producto", "categoria"], as_index=False)[col].sum()
              .sort_values(col))
        es_dinero = col != "unidades"
        pr["valor"] = pr[col] / 1e6 if es_dinero else pr[col]
        fig = px.bar(pr, x="valor", y="producto", orientation="h",
                     color_discrete_sequence=[AZUL],
                     hover_data={"categoria": True, "valor": ":,.1f"},
                     labels={"valor": "Millones COP" if es_dinero else "Unidades",
                             "producto": "", "categoria": "Categoría"},
                     title=f"Ranking de productos por {metrica.lower() if metrica else 'ventas'}")
        st.plotly_chart(estilo(fig, 460, leyenda=False), use_container_width=True)
    with b:
        ci = (d.groupby("ciudad", as_index=False)
              .agg(ventas=("venta_neta", "sum"), pedidos=("id_pedido", "count"))
              .sort_values("ventas"))
        ci["millones"] = ci["ventas"] / 1e6
        fig = px.bar(ci, x="millones", y="ciudad", orientation="h",
                     color_discrete_sequence=[AZUL],
                     hover_data={"pedidos": True, "millones": ":,.1f"},
                     labels={"millones": "Ventas (millones COP)", "ciudad": "",
                             "pedidos": "Pedidos"},
                     title="Ventas por ciudad")
        st.plotly_chart(estilo(fig, 300, leyenda=False), use_container_width=True)

        mix = (d.groupby(["canal", "categoria"])["venta_neta"].sum()
               .unstack(fill_value=0))
        mix = (mix.div(mix.sum(axis=1), axis=0) * 100).reindex(
            [c for c in ORDEN_CANAL if c in mix.index])
        fig = px.imshow(mix.round(1), text_auto=".0f", aspect="auto",
                        color_continuous_scale=["#f4f8fd", "#9ec5f4", "#2a78d6", "#0d366b"],
                        labels=dict(color="% ventas del canal", x="", y=""),
                        title="Mezcla de categorías por canal (%)")
        fig.update_xaxes(side="bottom", tickangle=-30)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(estilo(fig, 320, leyenda=False), use_container_width=True)

# --- 3. Distribución ------------------------------------------------------------
with t3:
    a, b = st.columns(2)
    with a:
        tope = d["venta_neta"].quantile(0.98)
        h = d[d["venta_neta"] <= tope]
        fig = px.histogram(h, x="venta_neta", nbins=40,
                           color_discrete_sequence=[AZUL],
                           labels={"venta_neta": "Valor del pedido (COP)"},
                           title="¿De cuánto es un pedido típico?")
        fig.add_vline(x=d["venta_neta"].median(), line_dash="dash",
                      line_color=GRIS,
                      annotation_text=f"Mediana {cop(d['venta_neta'].median())}",
                      annotation_position="top right")
        fig.update_traces(marker_line_color="white", marker_line_width=1,
                          hovertemplate="%{x}<br>%{y} pedidos<extra></extra>")
        fig.update_yaxes(title="Pedidos")
        st.plotly_chart(estilo(fig, 380, leyenda=False), use_container_width=True)
        st.caption("Se ocultan el 2% de pedidos más grandes (compras mayoristas) "
                   "para que se vea la forma de la distribución.")
    with b:
        dd = d[d["canal"] != "Tiendas propias"]
        if dd.empty:
            st.info("Las tiendas propias entregan en el momento; elige otro canal "
                    "para ver los tiempos de entrega.")
        else:
            fig = px.box(dd, x="canal", y="dias_entrega", color="canal",
                         color_discrete_map=COLOR_CANAL,
                         category_orders={"canal": ORDEN_CANAL},
                         labels={"dias_entrega": "Días de entrega", "canal": ""},
                         title="Tiempo de entrega por canal")
            st.plotly_chart(estilo(fig, 380, leyenda=False), use_container_width=True)
            st.caption("Tiendas propias no se incluye: la entrega es inmediata.")

    cal = (d.groupby(["canal", "calificacion"]).size()
           .rename("pedidos").reset_index())
    cal["%"] = cal["pedidos"] / cal.groupby("canal")["pedidos"].transform("sum") * 100
    fig = px.bar(cal, x="calificacion", y="%", color="canal", barmode="group",
                 color_discrete_map=COLOR_CANAL,
                 category_orders={"canal": ORDEN_CANAL},
                 labels={"calificacion": "Calificación del cliente (estrellas)",
                         "%": "% de pedidos del canal", "canal": "Canal"},
                 title="Distribución de la calificación del cliente por canal")
    fig.update_traces(hovertemplate="%{x} estrellas: %{y:.1f}%<extra>%{fullData.name}</extra>")
    st.plotly_chart(estilo(fig, 360), use_container_width=True)

# --- 4. Correlaciones -----------------------------------------------------------
with t4:
    a, b = st.columns(2)
    with a:
        vm = (d.groupby(["mes", "canal"], as_index=False)["venta_neta"].sum()
              .merge(mk, on=["mes", "canal"], how="inner"))
        vm["ventas_m"] = vm["venta_neta"] / 1e6
        vm["inv_m"] = vm["inversion_publicidad"] / 1e6
        fig = px.scatter(vm, x="inv_m", y="ventas_m", color="canal",
                         color_discrete_map=COLOR_CANAL,
                         category_orders={"canal": ORDEN_CANAL},
                         hover_data={"mes": "|%m/%Y"},
                         labels={"inv_m": "Inversión en publicidad del mes (millones COP)",
                                 "ventas_m": "Ventas del mes (millones COP)",
                                 "canal": "Canal", "mes": "Mes"},
                         title="Publicidad vs. ventas (cada punto es un mes)")
        fig.update_traces(marker=dict(size=10, line=dict(width=1.5, color="white")))
        fig.update_layout(legend=dict(orientation="h", y=-0.28, yanchor="top",
                                      x=0, xanchor="left", title_text=""))
        if len(vm) > 2:
            r = np.corrcoef(vm["inv_m"], vm["ventas_m"])[0, 1]
            fig = estilo(fig, 440)
            fig.update_layout(legend=dict(orientation="h", y=-0.28, yanchor="top", x=0))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Correlación de Pearson entre inversión y ventas: r = {num(r, 2)}. "
                       "Correlación no implica causalidad: los canales que más venden "
                       "también reciben más presupuesto.")
        else:
            st.plotly_chart(estilo(fig, 400), use_container_width=True)
    with b:
        de = (d[d["canal"] != "Tiendas propias"]
              .groupby("dias_entrega", as_index=False)
              .agg(calif=("calificacion", "mean"), devol=("devuelto", "mean"),
                   pedidos=("id_pedido", "count")))
        de = de[de["pedidos"] >= 20]
        fig = px.line(de, x="dias_entrega", y="calif", markers=True,
                      color_discrete_sequence=[AZUL],
                      hover_data={"pedidos": True},
                      labels={"dias_entrega": "Días de entrega",
                              "calif": "Calificación promedio", "pedidos": "Pedidos"},
                      title="A más días de entrega, peor calificación")
        fig.update_traces(line=dict(width=2.2), marker=dict(size=9))
        st.plotly_chart(estilo(fig, 400, leyenda=False), use_container_width=True)
        st.caption("Solo días con al menos 20 pedidos, para evitar promedios inestables.")

    num = d[["unidades", "descuento_pct", "venta_neta", "margen",
             "dias_entrega", "devuelto", "calificacion"]].rename(columns={
                 "unidades": "Unidades", "descuento_pct": "Descuento %",
                 "venta_neta": "Venta neta", "margen": "Margen",
                 "dias_entrega": "Días entrega", "devuelto": "Devuelto",
                 "calificacion": "Calificación"})
    corr = num.corr().round(2)
    fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
                    color_continuous_scale=["#c2410c", "#f4a582", "#f2f1ee",
                                            "#86b6ef", "#1c5cab"],
                    title="Matriz de correlación entre variables del pedido")
    fig.update_layout(coloraxis_colorbar=dict(title="r"))
    st.plotly_chart(estilo(fig, 430, leyenda=False), use_container_width=True)
    st.caption("Azul = relación positiva, naranja = negativa, gris = sin relación.")

# --- 5. Datos -------------------------------------------------------------------
with t5:
    st.markdown(f"**{len(d):,} pedidos** con los filtros actuales.".replace(",", "."))
    resumen = por_canal[["ventas", "participacion", "margen_pct", "pedidos",
                         "devol", "dias", "calif"]].copy()
    resumen.columns = ["Ventas (COP)", "Participación %", "Margen %", "Pedidos",
                       "Devolución %", "Días entrega", "Calificación"]
    resumen["Devolución %"] *= 100
    st.dataframe(resumen.style.format({
        "Ventas (COP)": lambda x: cop(x), "Participación %": "{:.1f}",
        "Margen %": "{:.1f}", "Devolución %": "{:.1f}",
        "Días entrega": "{:.1f}", "Calificación": "{:.2f}"}),
        use_container_width=True)
    st.dataframe(d.drop(columns=["mes"]).sort_values("fecha", ascending=False)
                 .head(500), use_container_width=True, hide_index=True,
                 column_config={"fecha": st.column_config.DateColumn("fecha", format="DD/MM/YYYY")})
    st.download_button("⬇️ Descargar datos filtrados (CSV)",
                       d.drop(columns=["mes"]).assign(fecha=d["fecha"].dt.date)
                       .to_csv(index=False).encode("utf-8-sig"),
                       file_name="nutriandes_filtrado.csv", mime="text/csv")

st.markdown('<p class="nota">PMV académico · Visualización de Datos · '
            'Politécnico Grancolombiano · NutriAndes S.A.S. es una empresa ficticia '
            'y todos los datos son simulados.</p>', unsafe_allow_html=True)
