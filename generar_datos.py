"""Genera los datos FICTICIOS de NutriAndes S.A.S. (empresa inventada).

Todos los valores son simulados con numpy (semilla fija, reproducible).
Salida: data/ventas.csv (un registro por pedido) y data/marketing.csv
(inversión publicitaria mensual por canal).
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(2026)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

meses = pd.period_range("2025-01", "2026-10", freq="M")

# Estacionalidad: enero (propósitos de año nuevo), noviembre (Black Friday),
# diciembre (navidad) y un leve repunte a mitad de año.
estac = {1: 1.30, 2: 1.05, 3: 1.00, 4: 0.95, 5: 0.98, 6: 1.05,
         7: 1.08, 8: 0.95, 9: 0.92, 10: 0.97, 11: 1.35, 12: 1.25}

# Canales: pedidos base/mes, crecimiento mensual, días de entrega, prob. devolución
canales = {
    "Ecommerce":       dict(base=190, crec=0.018, entrega=(2.5, 1.0), dev=0.045, uds=(1.6, 0.9), desc=0.10),
    "Mercado Libre":   dict(base=210, crec=0.032, entrega=(2.0, 0.9), dev=0.055, uds=(1.4, 0.7), desc=0.07),
    "Mayorista":       dict(base=28,  crec=0.006, entrega=(4.0, 1.5), dev=0.020, uds=(13, 5), desc=0.18),
    "Dropshipping":    dict(base=120, crec=0.015, entrega=(5.5, 2.0), dev=0.110, uds=(1.3, 0.6), desc=0.05),
    "Tiendas propias": dict(base=150, crec=-0.002, entrega=(0.0, 0.0), dev=0.015, uds=(1.8, 1.0), desc=0.06),
}

ciudades = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira", "Cartagena"]
p_ciudad = np.array([0.36, 0.20, 0.13, 0.10, 0.08, 0.07, 0.06])
p_ciudad_tiendas = np.array([0.55, 0.30, 0.15, 0, 0, 0, 0])  # tiendas solo en 3 ciudades

# Productos: categoría, precio de lista (COP), costo como % del precio
productos = [
    ("Proteína Whey 2 lb",        "Proteínas",        165000, 0.58),
    ("Proteína Vegana 1 kg",      "Proteínas",        189000, 0.55),
    ("Creatina Monohidratada",    "Rendimiento",       98000, 0.42),
    ("Pre-entreno Energy",        "Rendimiento",      115000, 0.45),
    ("Colágeno Hidrolizado",      "Bienestar",         89000, 0.38),
    ("Multivitamínico Diario",    "Vitaminas",         62000, 0.35),
    ("Vitamina C + Zinc",         "Vitaminas",         45000, 0.33),
    ("Omega 3",                   "Vitaminas",         72000, 0.40),
    ("Magnesio Citrato",          "Bienestar",         54000, 0.36),
    ("Quemador Termogénico",      "Control de peso",  105000, 0.40),
    ("Batido Reemplazo Comida",   "Control de peso",  138000, 0.50),
    ("Barras Proteicas x12",      "Snacks",            78000, 0.62),
]
p_prod = np.array([0.15, 0.06, 0.12, 0.07, 0.11, 0.09, 0.06, 0.07, 0.05, 0.08, 0.06, 0.08])

filas = []
pid = 100000
for i, m in enumerate(meses):
    for canal, c in canales.items():
        lam = c["base"] * (1 + c["crec"]) ** i * estac[m.month]
        n = rng.poisson(lam)
        dias_mes = m.days_in_month
        for _ in range(n):
            pid += 1
            fecha = m.start_time + pd.Timedelta(days=int(rng.integers(0, dias_mes)))
            pi = rng.choice(len(productos), p=p_prod)
            nombre, cat, precio, costo_pct = productos[pi]
            uds = max(1, int(round(rng.normal(*c["uds"]))))
            # Descuentos más altos en noviembre (Black Friday)
            d_media = c["desc"] + (0.10 if m.month == 11 else 0)
            desc = float(np.clip(rng.normal(d_media, 0.05), 0, 0.40))
            # Precio mayorista menor
            p_unit = precio * (0.78 if canal == "Mayorista" else 1.0) * rng.uniform(0.97, 1.03)
            venta = uds * p_unit * (1 - desc)
            costo = uds * precio * costo_pct * rng.uniform(0.95, 1.05)
            if canal == "Tiendas propias":
                ciudad = rng.choice(ciudades, p=p_ciudad_tiendas)
                dias = 0
            else:
                ciudad = rng.choice(ciudades, p=p_ciudad)
                extra = 1.5 if ciudad in ("Cartagena", "Barranquilla") else 0
                dias = int(max(1, round(rng.normal(c["entrega"][0] + extra, c["entrega"][1]))))
            # Más días de entrega -> más devoluciones y peor calificación
            p_dev = min(0.6, c["dev"] * (1 + 0.12 * max(0, dias - 3)))
            devuelto = int(rng.random() < p_dev)
            cal = 4.8 - 0.22 * max(0, dias - 2) - (1.4 if devuelto else 0) + rng.normal(0, 0.45)
            cal = int(np.clip(round(cal), 1, 5))
            filas.append(dict(
                id_pedido=pid, fecha=fecha.date(), canal=canal, ciudad=ciudad,
                categoria=cat, producto=nombre, unidades=uds,
                precio_unitario=round(p_unit), descuento_pct=round(desc * 100, 1),
                venta_neta=round(venta), costo=round(costo),
                dias_entrega=dias, devuelto=devuelto, calificacion=cal))

ventas = pd.DataFrame(filas).sort_values(["fecha", "id_pedido"]).reset_index(drop=True)
ventas.to_csv(OUT / "ventas.csv", index=False, encoding="utf-8")

# Inversión publicitaria mensual por canal: proporcional a la venta del mes + ruido
vm = (ventas.assign(mes=pd.to_datetime(ventas["fecha"]).dt.to_period("M").astype(str))
      .groupby(["mes", "canal"], as_index=False)["venta_neta"].sum())
pct_ads = {"Ecommerce": 0.11, "Mercado Libre": 0.08, "Mayorista": 0.015,
           "Dropshipping": 0.05, "Tiendas propias": 0.03}
vm["inversion_publicidad"] = (vm["venta_neta"] * vm["canal"].map(pct_ads)
                              * rng.normal(1, 0.18, len(vm))).round(-3).astype(int)
vm[["mes", "canal", "inversion_publicidad"]].to_csv(OUT / "marketing.csv", index=False)

print(len(ventas), "pedidos;", ventas["venta_neta"].sum() / 1e9, "mil millones")
print(ventas.groupby("canal")[["venta_neta", "devuelto", "dias_entrega", "calificacion"]].agg(
    {"venta_neta": "sum", "devuelto": "mean", "dias_entrega": "mean", "calificacion": "mean"}))
