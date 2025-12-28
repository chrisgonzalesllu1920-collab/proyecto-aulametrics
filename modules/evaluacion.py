import streamlit as st
import pandas as pd
import io
import analysis_core
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
import pedagogical_assistant

# --- CONFIGURACIÓN DE ESTÉTICA POWER BI ---
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

def evaluacion_page(asistente):
    inject_pbi_css()

    if not st.session_state.get('df_cargado', False):
        st.markdown("<h1 class='pbi-header'>Dashboard de Evaluación</h1>", unsafe_allow_html=True)
        configurar_uploader()
    else:
        tab1, tab2 = st.tabs(["Vista Global", "Perfil por Estudiante"])
        with tab1:
            mostrar_analisis_general(st.session_state.info_areas)
        with tab2:
            mostrar_analisis_por_estudiante()

def mostrar_analisis_general(results):
    st.markdown("<h2 class='pbi-header'>Resultados Consolidados</h2>", unsafe_allow_html=True)

    with st.sidebar:
        st.session_state.chart_type = st.radio(
            "Tipo de visualización",
            ["Barras", "Anillo", "Treemap"]
        )

    for area, result in results.items():
        competencias = result["competencias"]

        st.markdown(f"<div class='pbi-card'><b>{area}</b>", unsafe_allow_html=True)

        data = []
        for comp in competencias.values():
            total = comp["total_evaluados"]
            row = {"Competencia": comp["nombre_limpio"], "Total": total}
            for n in ["AD", "A", "B", "C"]:
                c = comp["conteo_niveles"].get(n, 0)
                row[f"{n}"] = c
                row[f"% {n}"] = round((c / total) * 100, 1) if total else 0
            data.append(row)

        df = pd.DataFrame(data).set_index("Competencia")

        styled = (
            df.style
            .set_properties(**{
                "border": "1px solid #D1D5DB",
                "text-align": "center"
            })
            .set_table_styles([
                {"selector": "th", "props": [
                    ("background-color", PBI_BLUE),
                    ("color", "white"),
                    ("font-weight", "bold"),
                    ("border", "1px solid #D1D5DB")
                ]}
            ])
        )

        st.dataframe(styled, use_container_width=True)

        excel = convert_df_to_excel(df, area, {})
        st.download_button(
            "Exportar a Excel",
            excel,
            f"Frecuencias_{area}.xlsx"
        )

        comp_sel = st.selectbox(
            "Seleccionar competencia",
            df.index,
            key=f"sel_{area}"
        )

        df_plot = df.loc[comp_sel, ["AD", "A", "B", "C"]].reset_index()
        df_plot.columns = ["Nivel", "Estudiantes"]

        if st.session_state.chart_type == "Barras":
            fig = px.bar(
                df_plot,
                x="Nivel",
                y="Estudiantes",
                color="Nivel",
                color_discrete_map=COLORS_NIVELES,
                text="Estudiantes"
            )
        elif st.session_state.chart_type == "Anillo":
            fig = px.pie(
                df_plot,
                names="Nivel",
                values="Estudiantes",
                hole=0.55,
                color="Nivel",
                color_discrete_map=COLORS_NIVELES
            )
        else:
            fig = px.treemap(
                df_plot,
                path=["Nivel"],
                values="Estudiantes",
                color="Nivel",
                color_discrete_map=COLORS_NIVELES
            )

        fig.update_layout(
            height=420,
            font_family="Segoe UI",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.05),
        )

        st.plotly_chart(fig, use_container_width=True)

        if st.button(f"Propuestas de mejora – {area}", key=f"ai_{area}"):
            texto = pedagogical_assistant.generate_suggestions(results, area, comp_sel)
            st.markdown(
                f"<div style='border-left:4px solid {PBI_LIGHT_BLUE};padding:12px;background:#F1F5F9'>{texto}</div>",
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

def mostrar_analisis_por_estudiante():
    st.markdown("<h2 class='pbi-header'>Perfil del Estudiante</h2>", unsafe_allow_html=True)

    dfs = st.session_state.all_dataframes
    first = next(iter(dfs.values()))
    col = first.columns[0]

    estudiante = st.selectbox("Seleccionar estudiante", first[col].unique())

    conteo = {"AD": 0, "A": 0, "B": 0, "C": 0}
    for df in dfs.values():
        fila = df[df[col] == estudiante]
        if not fila.empty:
            for v in fila.iloc[0].astype(str):
                if v in conteo:
                    conteo[v] += 1

    cols = st.columns(4)
    for i, n in enumerate(conteo):
        with cols[i]:
            st.markdown(
                f"<div style='background:{COLORS_NIVELES[n]};color:white;padding:16px;text-align:center'>"
                f"<div>{n}</div><div style='font-size:26px'>{conteo[n]}</div></div>",
                unsafe_allow_html=True
            )

    fig = px.bar(
        x=list(conteo.keys()),
        y=list(conteo.values()),
        color=list(conteo.keys()),
        color_discrete_map=COLORS_NIVELES
    )
    fig.update_layout(height=320, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def convert_df_to_excel(df, area_name, general_info):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Frecuencias")
        workbook = writer.book
        worksheet = writer.sheets["Frecuencias"]
        header = workbook.add_format({
            "bold": True,
            "bg_color": PBI_BLUE,
            "color": "white",
            "border": 1
        })
        for col_num, col_name in enumerate(df.columns, 1):
            worksheet.write(0, col_num, col_name, header)
    return output.getvalue()

def configurar_uploader():
    st.markdown("<div class='pbi-card'>", unsafe_allow_html=True)
    file = st.file_uploader("Cargar archivo SIAGIE", type=["xlsx"])
    if file:
        xls = pd.ExcelFile(file)
        hojas = [h for h in xls.sheet_names if h not in ["Generalidades", "Parametros"]]
        st.session_state.all_dataframes = {h: xls.parse(h) for h in hojas}
        st.session_state.info_areas = analysis_core.analyze_data(xls, hojas)
        st.session_state.df_cargado = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def inject_pbi_css():
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-color: {PBI_BG};
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
        margin-bottom: 16px;
    }}
    </style>
    """, unsafe_allow_html=True)


