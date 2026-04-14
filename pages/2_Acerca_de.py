"""
Página: Acerca de — OVDAS Fondos Concursables
"""
import streamlit as st

st.set_page_config(
    page_title="Acerca de — OVDAS Fondos",
    page_icon="🌋",
    layout="wide",
)

st.title("🌋 OVDAS — Observatorio Volcánico de los Andes del Sur")
st.caption("Sistema de monitoreo de fondos concursables / SERNAGEOMIN")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
## ¿Qué es este dashboard?

Sistema de búsqueda y monitoreo de **fondos concursables** — públicos, privados e internacionales —
relevantes para las actividades del Observatorio Volcánico de los Andes del Sur (OVDAS),
dependiente de SERNAGEOMIN.

### ¿Para qué sirve?

Permite identificar oportunidades de financiamiento para:

- 🔬 **Equipamiento científico** — sismógrafos, GPS geodésico, estaciones de monitoreo, cámaras termales, instrumentos de campo
- 🛰️ **Investigación** — proyectos de volcanología, geofísica, teledetección y ciencias de la tierra
- 💻 **Tecnología** — software de procesamiento de señales sísmicas, plataformas de datos abiertos, sistemas de alerta temprana
- 🤝 **Colaboración** — redes de investigación nacionales e internacionales, consorcios con universidades

### Cobertura

| Tipo | Fuentes |
|------|---------|
| Fondos públicos nacionales | ANID, GORE regionales (FIC-R), MMA, MinCiencia |
| Fondos internacionales | NASA, ESA, National Geographic, Horizon Europe, NSF |
| Fondos privados chilenos | BHP Foundation, Fundación Luksic, Minera Escondida |
| Tiempo real | fondos.gob.cl, datos.gob.cl |

### Cómo se calcula la relevancia

Cada fondo recibe un **score OVDAS de 0 a 100%** basado en:
- Coincidencia con palabras clave del área volcánica y geofísica
- Tipo de fondo (ciencia, equipamiento, innovación)
- Fondos objetivo explícitos del observatorio
- Cobertura regional (zonas con volcanes activos)

### Actualización

Los datos se actualizan periódicamente desde un sistema de monitoreo interno
que escanea múltiples fuentes dos veces al día.
""")

with col2:
    st.markdown("### 📊 Estadísticas del sistema")

    import pandas as pd, json
    from pathlib import Path

    csv_path = Path(__file__).parent.parent / "data" / "fondos_ovdas.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        df["score_ovdas"] = pd.to_numeric(df.get("score_ovdas", 0), errors="coerce").fillna(0)
        df["internacional"] = pd.to_numeric(df.get("internacional", 0), errors="coerce").fillna(0)

        st.metric("Total fondos OVDAS", len(df))
        st.metric("🟢 Abiertos ahora", len(df[df["estado"] == "abierto"]))
        st.metric("🟡 Próximos", len(df[df["estado"] == "proximo"]))
        st.metric("🌍 Internacionales", int(df["internacional"].sum()))
        st.metric("Score promedio", f"{df['score_ovdas'].mean():.0f}%")

        st.divider()
        st.markdown("**Top fondos por relevancia**")
        top = df.nlargest(5, "score_ovdas")[["nombre", "score_ovdas"]]
        for _, r in top.iterrows():
            score = int(r["score_ovdas"])
            st.progress(score / 100, text=f"{r['nombre'][:35]}... {score}%")

st.divider()

st.markdown("""
## 🗺️ Zonas de monitoreo volcánico activo

OVDAS monitorea los volcanes activos de Chile en las siguientes regiones,
todas con fondos GORE-FIC disponibles:

| Región | Volcanes principales |
|--------|---------------------|
| XV Arica y Parinacota | Parinacota, Taapaca |
| I Tarapacá | Isluga, Ollagüe |
| II Antofagasta | Láscar, San Pedro, Lastarria |
| III Atacama | Ojos del Salado |
| IX La Araucanía | Villarrica, Llaima, Lonquimay |
| XIV Los Ríos | Mocho-Choshuenco, Puyehue |
| X Los Lagos | Calbuco, Osorno, Chaiten |
| XI Aysén | Hudson, Cay, Mentolat |
| XII Magallanes | Lautaro, Reclus |

## 📬 Contacto

**OVDAS — Observatorio Volcánico de los Andes del Sur**
SERNAGEOMIN — Servicio Nacional de Geología y Minería
[www.sernageomin.cl](https://www.sernageomin.cl)

Red Nacional de Vigilancia Volcánica: [rnvv.sernageomin.cl](https://rnvv.sernageomin.cl)
""")
