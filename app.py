"""
Dashboard OVDAS — Fondos Concursables
Observatorio Volcánico de los Andes del Sur / SERNAGEOMIN

Versión pública desplegada en Streamlit Community Cloud.
Los datos se actualizan desde fondos_ovdas.csv (generado por el scanner local).
"""
import json
from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="OVDAS — Fondos Concursables",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.estado-abierto   { background:#16a34a; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; font-weight:bold; }
.estado-proximo   { background:#d97706; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; font-weight:bold; }
.estado-cerrado   { background:#dc2626; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; }
.estado-desconocido { background:#6b7280; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────
def badge_estado(estado: str) -> str:
    m = {"abierto": "🟢 ABIERTO", "proximo": "🟡 PRÓXIMO", "cerrado": "🔴 CERRADO"}
    return m.get(str(estado).lower(), "⚪ DESCONOCIDO")

def formato_monto(row) -> str:
    mn = row.get("monto_min")
    mx = row.get("monto_max")
    mon = row.get("moneda", "CLP")
    try: mn = float(mn) if mn and str(mn) not in ["", "nan", "None"] else None
    except: mn = None
    try: mx = float(mx) if mx and str(mx) not in ["", "nan", "None"] else None
    except: mx = None
    if not mn and not mx: return "—"
    if mn and mx:
        if mon == "CLP": return f"${mn/1_000_000:.0f}M – ${mx/1_000_000:.0f}M CLP"
        return f"{mn:,.0f} – {mx:,.0f} {mon}"
    if mx:
        if mon == "CLP": return f"hasta ${mx/1_000_000:.0f}M CLP"
        return f"hasta {mx:,.0f} {mon}"
    return "—"

def parse_list(val) -> list:
    if isinstance(val, list): return val
    if not val or str(val) in ["", "nan", "None", "[]"]: return []
    try: return json.loads(val)
    except: return []


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).parent / "data" / "fondos_ovdas.csv"
    if not csv_path.exists():
        st.error("No se encontró el archivo de datos.")
        return pd.DataFrame()
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["score_ovdas"] = pd.to_numeric(df.get("score_ovdas", 0), errors="coerce").fillna(0)
    df["internacional"] = pd.to_numeric(df.get("internacional", 0), errors="coerce").fillna(0)
    df["requisitos"] = df["requisitos"].apply(parse_list) if "requisitos" in df.columns else [[]] * len(df)
    return df.sort_values("score_ovdas", ascending=False)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌋 OVDAS")
    st.markdown("**Observatorio Volcánico de los Andes del Sur**")
    st.caption("SERNAGEOMIN — Fondos Concursables")
    st.divider()

    st.subheader("Filtros")

    estado_filter = st.multiselect(
        "Estado convocatoria",
        ["abierto", "proximo", "cerrado", "desconocido"],
        default=["abierto", "proximo"],
    )

    tipo_filter = st.multiselect(
        "Tipo de fondo",
        ["ciencia", "empresarial", "comunitario", "mixto", "cultural"],
        default=[],
    )

    solo_internacionales = st.checkbox("Solo internacionales", value=False)
    score_minimo = st.slider("Score OVDAS mínimo", 0, 100, 10)

    st.divider()
    st.caption("Los datos se actualizan periódicamente desde el sistema de monitoreo interno.")


# ─── Cargar datos ─────────────────────────────────────────────────────────────
df = load_data()

if df.empty:
    st.warning("Sin datos disponibles.")
    st.stop()

# ─── Aplicar filtros ──────────────────────────────────────────────────────────
filtered = df.copy()
if estado_filter:
    filtered = filtered[filtered["estado"].isin(estado_filter)]
if tipo_filter:
    filtered = filtered[filtered["tipo"].isin(tipo_filter)]
if solo_internacionales:
    filtered = filtered[filtered["internacional"] == 1]
filtered = filtered[filtered["score_ovdas"] >= score_minimo]


# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🌋 Fondos Concursables — OVDAS / SERNAGEOMIN")
st.caption("Oportunidades de financiamiento para equipamiento volcánico, investigación y monitoreo sísmico")

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Total fondos OVDAS", len(df))
with c2: st.metric("🟢 Abiertos", len(df[df["estado"] == "abierto"]))
with c3: st.metric("🟡 Próximos", len(df[df["estado"] == "proximo"]))
with c4: st.metric("🌍 Internacionales", int(df["internacional"].sum()))

st.divider()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_todos, tab_equipamiento, tab_ciencia, tab_colab, tab_desarrollo, tab_regionales, tab_tabla = st.tabs([
    "⭐ Todos por Prioridad",
    "🔬 Equipamiento",
    "🔭 Ciencia e I+D",
    "🤝 Colaboración",
    "🛰️ Desarrollo Instrumentos",
    "📍 Por Región",
    "📊 Tabla y Descarga",
])


# ─────────────────────────────────────
# TAB 1 — Todos por prioridad
# ─────────────────────────────────────
with tab_todos:
    st.caption(f"Mostrando {len(filtered)} fondos con score OVDAS ≥ {score_minimo}%")

    if filtered.empty:
        st.info("Sin fondos con los filtros actuales. Prueba bajar el score mínimo.")
    else:
        for _, row in filtered.iterrows():
            score = int(row.get("score_ovdas", 0))
            estado = str(row.get("estado", "desconocido")).lower()
            intl = "🌍 " if row.get("internacional", 0) == 1 else ""

            col_main, col_score = st.columns([4, 1])
            with col_main:
                st.markdown(
                    f"**{intl}{row.get('nombre','—')}** "
                    f"<span class='estado-{estado}'>{badge_estado(estado)}</span>",
                    unsafe_allow_html=True
                )
                st.caption(
                    f"🏛 {row.get('organismo','—')}  |  "
                    f"📁 {row.get('tipo','—')}  |  "
                    f"💰 {formato_monto(row)}"
                    + (f"  |  📍 {row['region']}" if str(row.get('region','')) not in ['','nan','None'] else "")
                )
                desc = str(row.get("descripcion", ""))
                if desc and desc not in ["", "nan", "None"]:
                    st.markdown(f"<small>{desc[:260]}{'...' if len(desc)>260 else ''}</small>",
                                unsafe_allow_html=True)
                reqs = parse_list(row.get("requisitos", []))
                if reqs:
                    st.caption("📋 " + " · ".join(reqs[:3]))
                if str(row.get("fecha_cierre","")) not in ["","nan","None"]:
                    st.caption(f"📅 Cierre: {row['fecha_cierre']}")
                if str(row.get("url","")) not in ["","nan","None"]:
                    st.markdown(f"[🔗 Ver convocatoria]({row['url']})")

            with col_score:
                color = "#22c55e" if score >= 60 else "#f59e0b" if score >= 30 else "#94a3b8"
                st.markdown(
                    f"<div style='text-align:center;padding-top:6px'>"
                    f"<span style='color:{color};font-size:1.4em;font-weight:bold'>{score}%</span>"
                    f"<br><small style='color:#94a3b8'>relevancia<br>OVDAS</small></div>",
                    unsafe_allow_html=True
                )
                st.progress(score / 100)

            st.divider()


# ─────────────────────────────────────
# TAB 2 — Equipamiento
# ─────────────────────────────────────
with tab_equipamiento:
    st.markdown("Fondos que permiten financiar **equipamiento científico** — sensores, sismógrafos, GPS, estaciones de monitoreo.")

    kw = ["equipamiento", "equipo", "instrumento", "sensor", "infraestructura", "tecnológico", "mediano", "mayor"]
    mask = df["nombre"].str.lower().str.contains("|".join(kw), na=False) | \
           df["descripcion"].fillna("").str.lower().str.contains("|".join(kw), na=False) | \
           df["tipo"].isin(["ciencia"])

    equip_df = df[mask].sort_values("score_ovdas", ascending=False)

    st.caption(f"{len(equip_df)} fondos identificados")
    for _, row in equip_df.iterrows():
        score = int(row.get("score_ovdas", 0))
        estado = str(row.get("estado", "desconocido")).lower()
        with st.expander(
            f"{'🟢' if estado=='abierto' else '🟡' if estado=='proximo' else '🔴'} "
            f"{row.get('nombre','—')} — {formato_monto(row)} — Score: {score}%",
            expanded=(estado == "abierto")
        ):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Organismo:** {row.get('organismo','—')}")
                st.write(f"**Monto:** {formato_monto(row)}")
                st.write(f"**Estado:** {badge_estado(estado)}")
                if str(row.get('region','')) not in ['','nan','None']:
                    st.write(f"**Región:** {row['region']}")
            with col_b:
                if str(row.get("fecha_cierre","")) not in ["","nan","None"]:
                    st.write(f"**Cierre:** {row['fecha_cierre']}")
                if str(row.get("url","")) not in ["","nan","None"]:
                    st.write(f"[🔗 Convocatoria]({row['url']})")
            desc = str(row.get("descripcion",""))
            if desc not in ["","nan","None"]:
                st.write(desc)
            reqs = parse_list(row.get("requisitos",[]))
            if reqs:
                st.write("**Requisitos:**")
                for r in reqs: st.write(f"  • {r}")
            st.progress(score / 100, text=f"Score OVDAS: {score}%")


# ─────────────────────────────────────
# TAB 3 — Ciencia e I+D
# ─────────────────────────────────────
with tab_ciencia:
    st.markdown("Fondos de **investigación, I+D e innovación** — ANID, NASA, ESA, Horizon Europe, FIC-R.")

    ciencia_df = df[df["tipo"].isin(["ciencia","mixto"])].sort_values("score_ovdas", ascending=False)

    for _, row in ciencia_df.iterrows():
        score = int(row.get("score_ovdas", 0))
        estado = str(row.get("estado","desconocido")).lower()
        intl = "🌍 " if row.get("internacional",0) == 1 else ""
        with st.expander(
            f"{'🟢' if estado=='abierto' else '🟡' if estado=='proximo' else '🔴'} "
            f"{intl}{row.get('nombre','—')} — Score: {score}%",
            expanded=(score >= 40 and estado in ["abierto","proximo"])
        ):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Organismo:** {row.get('organismo','—')}")
                st.write(f"**Monto:** {formato_monto(row)}")
                st.write(f"**Estado:** {badge_estado(estado)}")
            with col_b:
                if str(row.get("fecha_cierre","")) not in ["","nan","None"]:
                    st.write(f"**Cierre:** {row['fecha_cierre']}")
                if str(row.get("url","")) not in ["","nan","None"]:
                    st.write(f"[🔗 Convocatoria]({row['url']})")
            desc = str(row.get("descripcion",""))
            if desc not in ["","nan","None"]: st.write(desc)
            reqs = parse_list(row.get("requisitos",[]))
            if reqs:
                st.write("**Requisitos:**")
                for r in reqs: st.write(f"  • {r}")
            st.progress(score / 100, text=f"Score OVDAS: {score}%")


# ─────────────────────────────────────
# TAB 4 — Colaboración (SERNAGEOMIN + socios)
# ─────────────────────────────────────
with tab_colab:
    st.markdown("""
    **SERNAGEOMIN puede acceder a muchos fondos a través de COLABORACIONES estratégicas.**
    Estos fondos no son postulación directa — requieren un socio (universidad, municipio, GORE,
    institución internacional). Aquí están organizados por tipo de colaboración.
    """)

    # Detectar fondos colaborativos: empiezan con [COLABORACIÓN o requieren consorcio
    colab_mask = (
        df["descripcion"].fillna("").str.contains(r"\[COLABORACIÓN", case=False, regex=True) |
        df["descripcion"].fillna("").str.contains("consorcio|universidad|socio|alianza|contraparte",
                                                   case=False, regex=True)
    )
    colab_df = df[colab_mask].sort_values("score_ovdas", ascending=False)

    # Categorizar por tipo
    def _tipo_colab(desc: str) -> str:
        d = str(desc).lower()
        if "bilateral" in d or "japón" in d or "eeuu" in d or "alemania" in d:
            return "🌏 Internacional Bilateral"
        if "multilateral" in d or "undrr" in d or "naciones unidas" in d or "horizon" in d:
            return "🌐 Multilateral"
        if "gobierno-a-gobierno" in d or "bid" in d or "banco mundial" in d:
            return "🏛️ Gobierno-a-Gobierno"
        if "consorcio" in d or "universidad" in d or "anid" in d:
            return "🎓 Consorcio con Universidad"
        if "municipio" in d or "municipal" in d or "gore" in d:
            return "📍 GORE / Municipio"
        if "red científica" in d or "red internacional" in d or "smithsonian" in d or "gem" in d:
            return "🔬 Red Científica Internacional"
        return "🤝 Colaboración general"

    colab_df = colab_df.copy()
    colab_df["_categoria_colab"] = colab_df["descripcion"].apply(_tipo_colab)

    categorias = colab_df["_categoria_colab"].value_counts()
    st.caption(f"{len(colab_df)} fondos colaborativos identificados en {len(categorias)} categorías")

    # Mostrar cada categoría como expander
    for cat in categorias.index:
        fondos_cat = colab_df[colab_df["_categoria_colab"] == cat]
        with st.expander(f"{cat} — {len(fondos_cat)} fondos", expanded=True):
            for _, row in fondos_cat.iterrows():
                score = int(row.get("score_ovdas", 0))
                estado = str(row.get("estado", "desconocido")).lower()
                intl = "🌍 " if row.get("internacional", 0) == 1 else ""
                nombre = str(row.get('nombre','')).replace("[COLABORACIÓN] ", "")
                st.markdown(
                    f"**{intl}{nombre}** "
                    f"<span class='estado-{estado}'>{badge_estado(estado)}</span> "
                    f"— {formato_monto(row)} — Score OVDAS: {score}%",
                    unsafe_allow_html=True
                )
                desc = str(row.get("descripcion", "")).replace("[COLABORACIÓN", "**COLABORACIÓN").replace("] ", "** — ")
                st.caption(desc[:400] + ("..." if len(desc) > 400 else ""))
                reqs = parse_list(row.get("requisitos", []))
                if reqs:
                    st.caption("🔑 **Vía de acceso:** " + " · ".join(reqs[:3]))
                if str(row.get("url","")) not in ["","nan","None"]:
                    st.markdown(f"[🔗 Más info]({row['url']})")
                st.write("---")


# ─────────────────────────────────────
# TAB 5 — Desarrollo de Instrumentos en Chile
# ─────────────────────────────────────
with tab_desarrollo:
    st.markdown("""
    ### 🛰️ Desarrollo de Instrumentos Científicos en Chile

    En vez de comprar equipos importados (sismómetros, DOAS, multígas, cámaras termales),
    estos fondos permiten **desarrollar/fabricar instrumentos localmente** en consorcio con
    universidades chilenas. Esto crea capacidades nacionales, reduce dependencia de proveedores
    extranjeros, y genera transferencia tecnológica.

    **Instrumentos candidatos para desarrollo doméstico:**
    - 📡 Sismómetros de banda ancha (colaboración con depto. Geofísica UChile/USACH)
    - 🌫️ DOAS / Espectrómetros para gases volcánicos (UFRO, UdeC)
    - 🌋 Cámaras termales y sensores multígas (consorcio ingeniería electrónica)
    - 📶 Sistemas de telemetría satelital / LoRa para estaciones remotas
    """)

    # Filtrar fondos que financien I+D / desarrollo tecnológico
    dev_keywords = ["i+d", "i\\+d", "desarrollo", "innovación", "tecnología", "idea",
                     "fondef", "fondecyt", "anillos", "fic-r", "fondap", "corfo"]
    dev_mask = (
        df["nombre"].str.lower().str.contains("|".join(dev_keywords), na=False, regex=True) |
        df["tipo"].isin(["ciencia"])
    ) & (df["score_ovdas"] >= 30)
    dev_df = df[dev_mask].sort_values("score_ovdas", ascending=False)

    st.caption(f"{len(dev_df)} fondos aptos para desarrollo de instrumentos domésticos")

    for _, row in dev_df.iterrows():
        score = int(row.get("score_ovdas", 0))
        estado = str(row.get("estado", "desconocido")).lower()
        intl = "🌍 " if row.get("internacional", 0) == 1 else ""
        nombre = str(row.get('nombre','')).replace("[COLABORACIÓN] ", "")

        with st.expander(
            f"{'🟢' if estado=='abierto' else '🟡' if estado=='proximo' else '🔴'} "
            f"{intl}{nombre} — Score: {score}%",
            expanded=(score >= 70 and estado in ["abierto","proximo"])
        ):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Organismo:** {row.get('organismo','—')}")
                st.write(f"**Monto:** {formato_monto(row)}")
                st.write(f"**Estado:** {badge_estado(estado)}")
            with col_b:
                if str(row.get("fecha_cierre","")) not in ["","nan","None"]:
                    st.write(f"**Cierre:** {row['fecha_cierre']}")
                if str(row.get("url","")) not in ["","nan","None"]:
                    st.write(f"[🔗 Convocatoria]({row['url']})")

            desc = str(row.get("descripcion",""))
            if desc and desc not in ["","nan","None"]:
                st.write(desc)

            # Sugerencia de socios académicos
            st.info(
                "💡 **Socios académicos sugeridos:** Dpto. Geofísica UChile, "
                "Dpto. Ciencias Físicas UFRO, CIGIDEN (USACH/UCN/UTFSM/UC), "
                "CR2 (Center for Climate & Resilience), CSN (Centro Sismológico Nacional)"
            )


# ─────────────────────────────────────
# TAB 6 — Por Región Volcánica
# ─────────────────────────────────────
with tab_regionales:
    st.markdown("Fondos GORE en regiones con **volcanes activos** relevantes para monitoreo.")

    regiones_volcanicas = [
        "Arica y Parinacota","Tarapacá","Antofagasta","Atacama",
        "La Araucanía","Los Ríos","Los Lagos","Aysén","Magallanes","Biobío"
    ]

    reg_df = df[
        df["region"].isin(regiones_volcanicas) |
        df["organismo"].fillna("").str.contains("GORE", case=False)
    ].sort_values(["region","score_ovdas"], ascending=[True,False])

    regiones_presentes = sorted(reg_df["region"].dropna().unique())

    for region in regiones_presentes:
        fondos_reg = reg_df[reg_df["region"] == region]
        if fondos_reg.empty: continue
        with st.expander(f"📍 **{region}** — {len(fondos_reg)} fondos", expanded=False):
            for _, row in fondos_reg.iterrows():
                score = int(row.get("score_ovdas",0))
                estado = str(row.get("estado","desconocido")).lower()
                st.markdown(
                    f"**{row.get('nombre','—')}** "
                    f"<span class='estado-{estado}'>{badge_estado(estado)}</span> "
                    f"— {formato_monto(row)} — Score: {score}%",
                    unsafe_allow_html=True
                )
                if str(row.get("url","")) not in ["","nan","None"]:
                    st.markdown(f"[🔗 Ver convocatoria]({row['url']})")
                desc = str(row.get("descripcion",""))
                if desc not in ["","nan","None"]:
                    st.caption(desc[:150])
                st.write("---")

    # Nacionales sin región
    nacionales = df[
        df["region"].isna() &
        df["tipo"].isin(["ciencia","mixto"]) &
        (df["score_ovdas"] >= 20)
    ].sort_values("score_ovdas", ascending=False)

    if not nacionales.empty:
        with st.expander(f"🇨🇱 **Nacional** — {len(nacionales)} fondos sin región específica", expanded=False):
            for _, row in nacionales.iterrows():
                score = int(row.get("score_ovdas",0))
                estado = str(row.get("estado","desconocido")).lower()
                intl = "🌍 " if row.get("internacional",0) == 1 else ""
                st.markdown(
                    f"**{intl}{row.get('nombre','—')}** "
                    f"<span class='estado-{estado}'>{badge_estado(estado)}</span> "
                    f"— {formato_monto(row)} — Score: {score}%",
                    unsafe_allow_html=True
                )
                if str(row.get("url","")) not in ["","nan","None"]:
                    st.markdown(f"[🔗 Ver convocatoria]({row['url']})")
                st.write("---")


# ─────────────────────────────────────
# TAB 5 — Tabla y descarga
# ─────────────────────────────────────
with tab_tabla:
    cols_show = [c for c in [
        "nombre","organismo","tipo","estado","region",
        "monto_min","monto_max","moneda","score_ovdas",
        "internacional","fecha_cierre","url"
    ] if c in df.columns]

    tabla = filtered[cols_show].rename(columns={
        "nombre":"Fondo","organismo":"Organismo","tipo":"Tipo",
        "estado":"Estado","region":"Región",
        "monto_min":"Monto Mín","monto_max":"Monto Máx","moneda":"Moneda",
        "score_ovdas":"Score OVDAS","internacional":"Intl",
        "fecha_cierre":"Cierre","url":"URL",
    })

    st.dataframe(
        tabla,
        use_container_width=True,
        height=500,
        column_config={
            "Score OVDAS": st.column_config.ProgressColumn("🌋 Score OVDAS", min_value=0, max_value=100),
            "Intl": st.column_config.CheckboxColumn("🌍 Intl"),
            "URL": st.column_config.LinkColumn("🔗 URL"),
        }
    )

    csv_out = tabla.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("⬇️ Descargar CSV", csv_out, "fondos_ovdas.csv", "text/csv")
