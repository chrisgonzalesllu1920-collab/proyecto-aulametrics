import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pedagogical_assistant

# ================== CONFIGURACIÓN POWER BI GLOBAL ==================

PBI_BLUE = "#113770"
PBI_LIGHT_BLUE = "#0078D4"
PBI_BG = "#F9FAFB"
PBI_CARD_BG = "#FFFFFF"

COLORS_NIVELES = {
    'AD': '#008450',
    'A': '#32CD32',
    'B': '#FFB900',
    'C': '#E81123'
}

PBI_PLOTLY_TEMPLATE = dict(
    layout=dict(
        font=dict(family="Segoe UI", size=13, color="#1F2937"),
        title=dict(font=dict(size=16, color=PBI_BLUE), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1
        )
    )
)

# ================== PÁGINA PRINCIPAL ==================

def evaluacion_page(asistente):
    inject_pbi_css()

    if not st.session_state.get('df_cargado', False):
        st.markdown("<h1 class='pbi-header'>Dashboard de Evaluación</h1>", unsafe_allow_html=True)
        configurar_uploader()
    else:
        tab_global, tab_individual = st.tabs(["VISTA GLOBAL DEL AULA", "PERFIL POR ESTUDIANTE"])
        with tab_global:
            mostrar_analisis_general(st.session_state.get('info_areas', {}))
        with tab_individual:
            mostrar_analisis_por_estudiante(
                st.session_state.get('df'),
                st.session_state.get('df_config'),
                st.session_state.get('info_areas')
            )

# ================== ANÁLISIS GENERAL ==================

def mostrar_analisis_general(results):
    st.markdown("<h2 class='pbi-header'>Resultados Consolidados por Área</h2>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"<h3 style='color:{PBI_BLUE};'>Visualización</h3>", unsafe_allow_html=True)
        st.session_state.chart_type = st.radio(
            "Tipo de gráfico",
            ['Barras', 'Anillo', 'Treemap', 'Radar', 'Sunburst'],
            key="chart_radio_pbi"
        )

    tabs = st.tabs(list(results.keys()))

    for i, (sheet_name, result) in enumerate(results.items()):
        with tabs[i]:
            competencias = result.get('competencias', {})
            if not competencias:
                st.info("Sin datos")
                continue

            data = {'Competencia': [], 'AD': [], 'A': [], 'B': [], 'C': []}

            for c in competencias.values():
                data['Competencia'].append(c['nombre_limpio'])
                for n in ['AD', 'A', 'B', 'C']:
                    data[n].append(c['conteo_niveles'].get(n, 0))

            df = pd.DataFrame(data).set_index("Competencia")
            st.dataframe(df, use_container_width=True)

            st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
            comp = st.selectbox("Competencia", df.index, key=f"sel_{i}")

            df_plot = df.loc[comp].reset_index()
            df_plot.columns = ["Nivel", "Estudiantes"]

            fig = None

            if st.session_state.chart_type == 'Barras':
                fig = px.bar(
                    df_plot,
                    x="Nivel",
                    y="Estudiantes",
                    color="Nivel",
                    text="Estudiantes",
                    color_discrete_map=COLORS_NIVELES,
                    template=PBI_PLOTLY_TEMPLATE
                )

            elif st.session_state.chart_type == 'Anillo':
                fig = px.pie(
                    df_plot,
                    values="Estudiantes",
                    names="Nivel",
                    hole=0.6,
                    color="Nivel",
                    color_discrete_map=COLORS_NIVELES,
                    template=PBI_PLOTLY_TEMPLATE
                )

            elif st.session_state.chart_type == 'Treemap':
                fig = px.treemap(
                    df_plot,
                    path=["Nivel"],
                    values="Estudiantes",
                    color="Nivel",
                    color_discrete_map=COLORS_NIVELES,
                    template=PBI_PLOTLY_TEMPLATE
                )

            elif st.session_state.chart_type == 'Radar':
                fig = go.Figure(
                    go.Scatterpolar(
                        r=df_plot["Estudiantes"],
                        theta=df_plot["Nivel"],
                        fill="toself",
                        line_color=PBI_LIGHT_BLUE
                    )
                )
                fig.update_layout(template=PBI_PLOTLY_TEMPLATE)

            elif st.session_state.chart_type == 'Sunburst':
                fig = px.sunburst(
                    df_plot,
                    path=["Nivel"],
                    values="Estudiantes",
                    color="Nivel",
                    color_discrete_map=COLORS_NIVELES,
                    template=PBI_PLOTLY_TEMPLATE
                )

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ================== PERFIL ESTUDIANTE ==================

def mostrar_analisis_por_estudiante(df_first, df_config, info_areas):
    st.markdown("<h2 class='pbi-header'>Perfil del Estudiante</h2>", unsafe_allow_html=True)

    all_dfs = st.session_state.get("all_dataframes", {})
    if not all_dfs:
        return

    df_base = next(iter(all_dfs.values()))
    col = next(c for c in df_base.columns if "NOMBRE" in str(c).upper())

    estudiante = st.selectbox("Estudiante", df_base[col].dropna().unique())

    total = dict.fromkeys(['AD', 'A', 'B', 'C'], 0)

    for df in all_dfs.values():
        fila = df[df[col] == estudiante]
        if not fila.empty:
            for v in fila.iloc[0]:
                if str(v).upper() in total:
                    total[str(v).upper()] += 1

    cols = st.columns(4)
    for i, n in enumerate(total):
        cols[i].markdown(
            f"<div style='background:{COLORS_NIVELES[n]};padding:16px;color:white;text-align:center;'>"
            f"<b>{n}</b><br>{total[n]}</div>",
            unsafe_allow_html=True
        )

    fig = px.pie(
        values=total.values(),
        names=total.keys(),
        hole=0.5,
        color=total.keys(),
        color_discrete_map=COLORS_NIVELES,
        template=PBI_PLOTLY_TEMPLATE
    )
    st.plotly_chart(fig, use_container_width=True)

# ================== EXCEL ==================

@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer)
    return output.getvalue()

# ================== UPLOADER ==================

def configurar_uploader():
    file = st.file_uploader("Archivo Excel", type=["xlsx"])
    if file:
        excel = pd.ExcelFile(file)
        hojas = [s for s in excel.sheet_names if s not in ["Generalidades", "Parametros"]]
        st.session_state.all_dataframes = {h: excel.parse(h) for h in hojas}
        st.session_state.info_areas = analysis_core.analyze_data(excel, hojas)
        st.session_state.df_cargado = True
        st.rerun()

# ================== CSS POWER BI ==================

def inject_pbi_css():
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-color: {PBI_BG} !important;
    }}
    .pbi-card {{
        background: white;
        padding: 24px;
        border: 1px solid #E5E7EB;
        margin-bottom: 24px;
    }}
    .pbi-header {{
        color: {PBI_BLUE};
        font-weight: 700;
        border-bottom: 4px solid {PBI_LIGHT_BLUE};
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

