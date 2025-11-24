import json
from streamlit_lottie import st_lottie
import streamlit as st
import pandas as pd
import analysis_core
import pedagogical_assistant
import plotly.express as px
import io 
import xlsxwriter 
import os 
import base64 
from supabase import create_client, Client
# --- FUNCIÓN PARA CARGAR ROBOTS (LOTTIE) ---
def cargar_lottie(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

# =========================================================================
# === 1. CONFIGURACIÓN INICIAL ===
# =========================================================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
  page_title="AulaMetrics", 
  page_icon="assets/isotipo.png",
  layout="wide",
  initial_sidebar_state="collapsed"
)

# 👇👇👇 PEGA ESTO AQUÍ ARRIBA 👇👇👇
# --- ESTILOS CSS: BOTÓN AZUL Y LIMPIEZA ---
st.markdown("""
    <style>
    /* Ocultar cadenas */
    h1 > a, h2 > a, h3 > a {display: none !important;}
    footer {visibility: hidden;}
    
    /* ESTILO BOTÓN AZUL */
    div[data-testid="stDownloadButton"] > button {
        background-color: #007bff !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #0056b3 !important;
    }
    </style>
""", unsafe_allow_html=True)
# 👆👆👆 FIN DEL ESTILO 👆👆👆

@st.cache_data 
def get_image_as_base64(file_path):
  """Carga una imagen y la convierte a Base64 string."""
  try:
      with open(file_path, "rb") as f:
          data = f.read()
      return base64.b64encode(data).decode()
  except FileNotFoundError:
      return None
      
# =========================================================================
# === 2. INICIALIZACIÓN SUPABASE Y ESTADO ===
# =========================================================================
try:
    supabase_url = st.secrets['supabase']['url']
    supabase_key = st.secrets['supabase']['anon_key']
    supabase: Client = create_client(supabase_url, supabase_key)
except KeyError:
    st.error("Error: Faltan las claves de Supabase en 'secrets.toml'.")
    st.stop()
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

if 'logged_in' not in st.session_state:
  st.session_state.logged_in = False
  
if 'show_welcome_message' not in st.session_state:
  st.session_state.show_welcome_message = False
  
if 'df_cargado' not in st.session_state:
  st.session_state.df_cargado = False

if 'df' not in st.session_state:
  st.session_state.df = None
if 'df_config' not in st.session_state:
  st.session_state.df_config = None
if 'info_areas' not in st.session_state:
  st.session_state.info_areas = None

# =========================================================================
# === 3. ESTILOS CSS ===
# =========================================================================
st.markdown("""
<style>
    div.st-block-container { padding-top: 2rem; }
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap');

    .gradient-title-login, .gradient-title-dashboard {
        font-family: 'Oswald', sans-serif;
        font-weight: 700;
        background: linear-gradient(45deg, #00BFA5, #2196F3);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        -webkit-text-fill-color: transparent; 
        display: inline-block;
    }
    @supports not (-webkit-background-clip: text) {
        .gradient-title-login, .gradient-title-dashboard {
            color: #2196F3; 
            background: none;
        }
    }
    
    .gradient-title-dashboard { font-size: 2.5em; }
    
    div[data-testid="stTextInput"] input:focus {
        background-color: #FFFFE0;
        border: 2px solid #FFD700;
        box-shadow: 0 0 5px #FFD700;
    }
    
    [data-testid="stExpander"] summary {
        background-color: #00BFA5;
        color: white !important;
        border-radius: 5px;
        padding: 10px 15px;
        font-weight: 600;
    }
    [data-testid="stExpander"] summary svg { fill: white !important; }
    [data-testid="stExpander"] summary:hover {
        background-color: #008f7a;
        color: white !important;
    }
    
    .hero-container {
        text-align: center;
        padding: 0.2rem 0 2rem 0; 
    }
    .hero-logo {
        width: 120px;
        height: 120px;
        margin-bottom: 1rem;
    }
    .gradient-title-login { font-size: 5.0em; line-height: 1.1; }
    
    div.st-block-container > div:first-child { max-width: 100% !important; }
    [data-testid="stFullScreenButton"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# === 4. PÁGINA DE LOGIN ===
# =========================================================================
def login_page():
    col1, col_centro, col3 = st.columns([1, 2, 1])
    
    with col_centro:
        st.image("assets/logotipo-aulametrics.png", width=300)
        st.subheader("Bienvenido a AulaMetrics", anchor=False)
        st.markdown("Tu asistente pedagógico y analista de datos.")
        
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarme"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Correo Electrónico", key="login_email")
                password = st.text_input("Contraseña", type="password", key="login_password")
                submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True, type="primary")
                
                if submitted:
                    try:
                        session = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        st.session_state.logged_in = True
                        st.session_state.user = session.user
                        st.session_state.show_welcome_message = True
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error al iniciar sesión: {e}")

        with tab_register:
            with st.form("register_form"):
                name = st.text_input("Nombre", key="register_name")
                email = st.text_input("Correo Electrónico", key="register_email")
                password = st.text_input("Contraseña", type="password", key="register_password")
                submitted = st.form_submit_button("Registrarme", use_container_width=True)
                
                if submitted:
                    if not name or not email or not password:
                        st.warning("Por favor, completa todos los campos.")
                    else:
                        try:
                            user = supabase.auth.sign_up({
                                "email": email,
                                "password": password,
                                "options": {
                                    "data": { 'full_name': name }
                                }
                            })
                            st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
                            st.info("Ve a la pestaña 'Iniciar Sesión' para ingresar.")
                        except Exception as e:
                            st.error(f"Error en el registro: {e}")

        st.divider()
        
        # URL de tu página de github
        url_netlify = "https://chrisgonzalesllu1920-collab.github.io/aulametrics-landing/" 
        
        st.markdown(f"""
        <a href="{url_netlify}" target="_blank" style="
            display: inline-block;
            width: 100%;
            padding: 10px 0;
            background-color: #0068C9; /* Azul Profesional */
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            box-sizing: border-box; 
        ">
            ¿Dudas? Contáctanos (WhatsApp/TikTok/Email)
        </a>
        """, unsafe_allow_html=True)

# =========================================================================
# === 5. FUNCIONES AUXILIARES ===
# =========================================================================
ISOTIPO_PATH = "assets/isotipo.png"
RUTA_ESTANDARES = "assets/Estandares de aprendizaje.xlsx" 

@st.cache_data(ttl=3600)
def cargar_datos_pedagogicos():
    try:
        df_generalidades = pd.read_excel(RUTA_ESTANDARES, sheet_name="Generalidades")
        df_ciclos = pd.read_excel(RUTA_ESTANDARES, sheet_name="Cicloseducativos")
        df_desc_sec = pd.read_excel(RUTA_ESTANDARES, sheet_name="Descriptorsecundaria")
        df_desc_prim = pd.read_excel(RUTA_ESTANDARES, sheet_name="Descriptorprimaria")
        
        df_generalidades['NIVEL'] = df_generalidades['NIVEL'].ffill()
        df_ciclos['ciclo'] = df_ciclos['ciclo'].ffill()
        
        columna_estandar = "DESCRIPCIÓN DE LOS NIVELES DEL DESARROLLO DE LA COMPETENCIA"
        
        cols_to_fill_prim = ['Área', 'Competencia', 'Ciclo', columna_estandar]
        cols_to_fill_sec = ['Área', 'Competencia', 'Ciclo', columna_estandar]
        
        df_desc_prim[cols_to_fill_prim] = df_desc_prim[cols_to_fill_prim].ffill()
        df_desc_sec[cols_to_fill_sec] = df_desc_sec[cols_to_fill_sec].ffill()
        
        return df_generalidades, df_ciclos, df_desc_sec, df_desc_prim
    
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo en la ruta: {RUTA_ESTANDARES}")
        return None, None, None, None
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        return None, None, None, None

# --- FUNCIÓN (UPLOADER) - v3.0 MULTI-HOJA ---
def configurar_uploader():
    """
    Procesa el archivo Excel.
    AHORA GUARDA TODAS LAS HOJAS EN MEMORIA para el análisis integral.
    """
    uploaded_file = st.file_uploader(
        "Sube tu archivo de Excel aquí", 
        type=["xlsx", "xls"], 
        key="file_uploader"
    )

    if uploaded_file is not None:
        with st.spinner('Procesando todas las áreas...'):
            try:
                # 1. Leer el archivo Excel
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
                
                # 2. Filtrar hojas que no son áreas (Generalidades, etc.)
                IGNORE_SHEETS = [analysis_core.GENERAL_SHEET_NAME.lower(), 'parametros', 'generalidades']
                valid_sheets = [name for name in sheet_names if name.lower() not in IGNORE_SHEETS]

                # 3. Ejecutar análisis de frecuencias (Tab 1)
                results_dict = analysis_core.analyze_data(excel_file, valid_sheets)
                st.session_state.info_areas = results_dict
                st.session_state.df_cargado = True
                
                # --- 4. ¡LA CLAVE! LEER Y GUARDAR TODAS LAS HOJAS ---
                # Creamos un diccionario donde guardaremos: {'Matemática': df_mate, 'Arte': df_arte...}
                all_dataframes = {}
                
                for sheet in valid_sheets:
                    try:
                        # Leemos cada hoja individualmente
                        df_temp = pd.read_excel(uploaded_file, sheet_name=sheet, header=0)
                        all_dataframes[sheet] = df_temp
                    except:
                        pass # Si una hoja falla, la saltamos para no romper todo
                
                # Guardamos este "Tesoro" en la memoria de la App
                st.session_state.all_dataframes = all_dataframes

                # Mantenemos st.session_state.df solo para compatibilidad (usamos la primera hoja)
                if valid_sheets:
                    st.session_state.df = all_dataframes[valid_sheets[0]]
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
                st.session_state.df_cargado = False

def mostrar_analisis_general(results):
    st.markdown("---")
    st.subheader("Resultados Consolidados por Área")

    first_sheet_key = next(iter(results), None)
    general_data = {}
    if first_sheet_key and 'generalidades' in results[first_sheet_key]:
        general_data = results[first_sheet_key]['generalidades']
        st.info(f"Datos del Grupo: Nivel: **{general_data.get('nivel', 'Desconocido')}** | Grado: **{general_data.get('grado', 'Desconocido')}**")
    
    st.sidebar.subheader("⚙️ Configuración del Gráfico")
    
    chart_options = ('Barras (Por Competencia)', 'Pastel (Proporción)')
    st.session_state.chart_type = st.sidebar.radio("Elige el tipo de visualización:", chart_options, key="chart_radio_premium")

    tabs = st.tabs([f"Área: {sheet_name}" for sheet_name in results.keys()])

    for i, (sheet_name, result) in enumerate(results.items()):
        with tabs[i]:
            if 'error' in result:
                st.error(f"Error al procesar la hoja '{sheet_name}': {result['error']}")
                continue
            competencias = result['competencias']
            if not competencias:
                st.info(f"No se encontraron datos de competencias en la hoja '{sheet_name}'.")
                continue

            st.markdown("##### 1. Distribución de Logros")
            
            data = {'Competencia': [], 'AD (Est.)': [], '% AD': [], 'A (Est.)': [], '% A': [], 'B (Est.)': [], '% B': [], 'C (Est.)': [], '% C': [], 'Total': []}
            
            for col_original_name, comp_data in competencias.items():
                counts = comp_data['conteo_niveles']
                total = comp_data['total_evaluados']
                data['Competencia'].append(comp_data['nombre_limpio']) 
                for level in ['AD', 'A', 'B', 'C']:
                    count = counts.get(level, 0)
                    porcentaje = (count / total * 100) if total > 0 else 0
                    data[f'{level} (Est.)'].append(count)
                    data[f'% {level}'].append(f"{porcentaje:.1f}%")
                data['Total'].append(total)
            df_table = pd.DataFrame(data).set_index('Competencia')
            st.dataframe(df_table)
            
            excel_data = convert_df_to_excel(df_table, sheet_name, general_data)
            st.download_button(label=f"⬇️ Exportar Excel ({sheet_name})", data=excel_data, file_name=f'Frecuencias_{sheet_name}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key=f'download_excel_{sheet_name}')

            st.markdown("---")
            competencia_nombres_limpios = df_table.index.tolist()
            selected_comp = None 

            if st.session_state.chart_type == 'Barras (Por Competencia)':
                selected_comp = st.selectbox(f"Selecciona la competencia:", options=competencia_nombres_limpios, key=f'select_comp_bar_{sheet_name}')
                df_bar_data = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']].rename(index={'AD (Est.)': 'AD', 'A (Est.)': 'A', 'B (Est.)': 'B', 'C (Est.)': 'C'})
                df_bar = df_bar_data.reset_index()
                df_bar.columns = ['Nivel', 'Estudiantes']
                fig = px.bar(df_bar, x='Nivel', y='Estudiantes', title=f"Logros: {selected_comp}", color='Nivel', color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)
            
            elif st.session_state.chart_type == 'Pastel (Proporción)':
                selected_comp = st.selectbox(f"Selecciona la competencia:", options=competencia_nombres_limpios, key=f'select_comp_pie_{sheet_name}')
                data_pie_data = df_table.loc[selected_comp, ['AD (Est.)', 'A (Est.)', 'B (Est.)', 'C (Est.)']]
                data_pie = data_pie_data.reset_index()
                data_pie.columns = ['Nivel', 'Estudiantes']
                fig = px.pie(data_pie, values='Estudiantes', names='Nivel', title=f"Proporción: {selected_comp}", color='Nivel', color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'})
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            if selected_comp:
                st.session_state[f'selected_comp_{sheet_name}'] = selected_comp
            selected_comp_key = f'selected_comp_{sheet_name}'
            
            if st.button(f"🎯 Propuestas de mejora", key=f"asistente_comp_{sheet_name}", type="primary"):
                if selected_comp_key in st.session_state and st.session_state[selected_comp_key]:
                    comp_name_limpio = st.session_state[selected_comp_key]
                    with st.expander(f"Ver Propuestas de mejora para: {comp_name_limpio}", expanded=True):
                        ai_report_text = pedagogical_assistant.generate_suggestions(results, sheet_name, comp_name_limpio)
                        st.markdown(ai_report_text, unsafe_allow_html=True)
                else:
                    st.warning("Selecciona una competencia en el desplegable de gráficos.")

# =========================================================================
# === FUNCIÓN (TAB 2: ANÁLISIS POR ESTUDIANTE) - v5.0 FINAL CON WORD ===
# =========================================================================
def mostrar_analisis_por_estudiante(df_first, df_config, info_areas):
    """
    Muestra el perfil INTEGRAL y permite descargar INFORME WORD.
    """
    st.markdown("---")
    st.header("🧑‍🎓 Perfil Integral del Estudiante")
    
    if 'all_dataframes' not in st.session_state or not st.session_state.all_dataframes:
        st.warning("⚠️ No se han cargado datos. Sube un archivo en la Pestaña 1.")
        return

    all_dfs = st.session_state.all_dataframes
    
    # 1. DETECCIÓN DE COLUMNA
    posibles_nombres = [
        "Estudiante", "ESTUDIANTE", "APELLIDOS Y NOMBRES", "Apellidos y Nombres", 
        "ALUMNO", "Alumno", "Nombres y Apellidos", "Nombre Completo", 
        "Nombres", "NOMBRES"
    ]
    
    first_sheet_name = next(iter(all_dfs))
    df_base = all_dfs[first_sheet_name]
    
    col_nombre = None
    for col in df_base.columns:
        if str(col).strip() in posibles_nombres:
            col_nombre = col
            break
    
    if not col_nombre:
        st.error(f"❌ No encontramos la columna de nombres en la hoja '{first_sheet_name}'.")
        return

    # 2. SELECTOR
    lista_estudiantes = df_base[col_nombre].dropna().unique()
    estudiante_sel = st.selectbox("🔍 Busca al estudiante:", options=lista_estudiantes, index=None, placeholder="Escribe nombre...")

    if estudiante_sel:
        st.divider()
        st.subheader(f"📊 Reporte Global: {estudiante_sel}")
        
        # --- 3. BARRIDO CON MEMORIA DE ÁREAS ---
        total_conteo = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
        desglose_areas = {'AD': [], 'A': [], 'B': [], 'C': []}
        areas_analizadas = 0
        
        # Barra de progreso
        my_bar = st.progress(0, text="Analizando áreas...")
        total_sheets = len(all_dfs)
        
        for i, (area_name, df_area) in enumerate(all_dfs.items()):
            my_bar.progress((i + 1) / total_sheets, text=f"Revisando: {area_name}")
            
            c_name_local = None
            for c in df_area.columns:
                if str(c).strip() in posibles_nombres:
                    c_name_local = c
                    break
            
            if c_name_local:
                fila = df_area[df_area[c_name_local] == estudiante_sel]
                if not fila.empty:
                    areas_analizadas += 1
                    vals = [str(v).upper().strip() for v in fila.iloc[0].values]
                    
                    c_ad = vals.count('AD')
                    c_a = vals.count('A')
                    c_b = vals.count('B')
                    c_c = vals.count('C')
                    
                    total_conteo['AD'] += c_ad
                    total_conteo['A'] += c_a
                    total_conteo['B'] += c_b
                    total_conteo['C'] += c_c
                    
                    if c_ad > 0: desglose_areas['AD'].append(f"{area_name} ({c_ad})")
                    if c_a > 0: desglose_areas['A'].append(f"{area_name} ({c_a})")
                    if c_b > 0: desglose_areas['B'].append(f"{area_name} ({c_b})")
                    if c_c > 0: desglose_areas['C'].append(f"{area_name} ({c_c})")

        my_bar.empty()
        
        # --- 4. MOSTRAR RESULTADOS CON DETALLE ---
        suma_total = sum(total_conteo.values())
        
        col_izq, col_der = st.columns([1, 1.5])
        
        with col_izq:
            st.markdown("#### 📈 Detalle por Nivel")
            st.caption(f"Se analizaron {areas_analizadas} áreas en total.")
            
            # AD
            if total_conteo['AD'] > 0:
                with st.expander(f"🏆 Logro Destacado (AD): {total_conteo['AD']}", expanded=False):
                    for area in desglose_areas['AD']: st.markdown(f"- {area}")
            else:
                st.markdown(f"🏆 **AD:** 0")

            # A
            if total_conteo['A'] > 0:
                with st.expander(f"✅ Logro Esperado (A): {total_conteo['A']}", expanded=False):
                    for area in desglose_areas['A']: st.markdown(f"- {area}")
            else:
                st.markdown(f"✅ **A:** 0")

            # B
            if total_conteo['B'] > 0:
                with st.expander(f"⚠️ En Proceso (B): {total_conteo['B']}", expanded=True):
                    st.markdown("**:orange[Áreas a reforzar:]**")
                    for area in desglose_areas['B']: st.markdown(f"- {area}")
            else:
                st.markdown(f"⚠️ **B:** 0")

            # C
            if total_conteo['C'] > 0:
                with st.expander(f"🛑 En Inicio (C): {total_conteo['C']}", expanded=True):
                    st.markdown("**:red[Requiere atención urgente en:]**")
                    for area in desglose_areas['C']: st.markdown(f"- {area}")
            else:
                st.markdown(f"🛑 **C:** 0")

        with col_der:
            if suma_total > 0:
                df_chart = pd.DataFrame({'Nivel': list(total_conteo.keys()), 'Cantidad': list(total_conteo.values())})
                df_chart = df_chart[df_chart['Cantidad'] > 0]
                fig = px.pie(
                    df_chart, values='Cantidad', names='Nivel', 
                    title=f"Mapa de Calor Académico",
                    color='Nivel',
                    color_discrete_map={'AD': 'green', 'A': 'lightgreen', 'B': 'orange', 'C': 'red'},
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin registros de notas.")

        # --- 5. BOTÓN DE DESCARGA DE INFORME (NUEVO) ---
        st.write("---")
        st.write("#### 📥 Opciones de Exportación")
        
        if suma_total > 0:
            # Llamamos a la función que creamos en pedagogical_assistant.py
            # Asumimos que lo tienes importado como 'pedagogical_assistant'
            import pedagogical_assistant # Importación local por seguridad
            
            with st.spinner("Generando informe en Word..."):
                doc_buffer = pedagogical_assistant.generar_reporte_estudiante(
                    estudiante_sel, 
                    total_conteo, 
                    desglose_areas
                )
            
# 1. INSERTAMOS EL ESTILO AZUL (CSS)
            st.markdown("""
                <style>
                div.stDownloadButton > button:first-child {
                    background-color: #0056b3; /* Azul Profesional */
                    color: white;
                    border-radius: 8px;
                    border: 1px solid #004494;
                }
                div.stDownloadButton > button:first-child:hover {
                    background-color: #004494; /* Azul más oscuro al pasar el mouse */
                    color: white;
                    border-color: #002a5c;
                }
                </style>
            """, unsafe_allow_html=True)

            # 2. EL BOTÓN (Sin type="primary")
            st.download_button(
                label="📄 Descargar Informe de Progreso (Word)",
                data=doc_buffer,
                file_name=f"Informe_Progreso_{estudiante_sel}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
                # Nota: He borrado la línea 'type="primary"' para que el azul funcione
            )

# --- FUNCIÓN (Conversión a Excel) - MEJORADA (Colores y Anchos) ---
@st.cache_data
def convert_df_to_excel(df, area_name, general_info):
    """
    Convierte DataFrame a formato Excel (xlsx) con formato profesional:
    - Columna de Competencias ancha.
    - Encabezados de colores (AD=Verde, B=Naranja, C=Rojo).
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 1. Escribir las hojas
        workbook = writer.book
        
        # --- Hoja Generalidades ---
        info_sheet = workbook.add_worksheet("Generalidades")
        bold_fmt = workbook.add_format({'bold': True})
        info_sheet.write('A1', 'Área:', bold_fmt)
        info_sheet.write('B1', area_name)
        info_sheet.write('A2', 'Nivel:', bold_fmt)
        info_sheet.write('B2', general_info.get('nivel', 'N/A'))
        info_sheet.write('A3', 'Grado:', bold_fmt)
        info_sheet.write('B3', general_info.get('grado', 'N/A'))
        
        # --- Hoja Frecuencias (Aquí está la magia) ---
        df.to_excel(writer, sheet_name='Frecuencias', startrow=0, startcol=0, index=True)
        worksheet = writer.sheets['Frecuencias']

        # 2. Definir Formatos de Colores (Estilo Pastel Profesional)
        # AD y A (Verdes)
        fmt_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # B (Naranja/Amarillo)
        fmt_orange = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # C (Rojo)
        fmt_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # Cabecera Genérica (Gris)
        fmt_header = workbook.add_format({'bg_color': '#D3D3D3', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        # Texto normal (Alineado a la izquierda para competencias)
        fmt_text = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})

        # 3. Ajustar Ancho de Columnas
        # Columna A (Índice/Competencia): Muy ancha (60)
        worksheet.set_column('A:A', 60, fmt_text)
        # Columnas B en adelante (Datos): Ancho estándar (15) y centradas
        worksheet.set_column('B:Z', 15)

        # 4. Pintar los Encabezados con Lógica
        # (Sobrescribimos la fila 0 con los colores correctos)
        
        # Primero pintamos la celda A1 (El título "Competencia")
        worksheet.write(0, 0, "Competencia", fmt_header)

        # Ahora recorremos las columnas de datos (AD, % AD, etc.)
        # df.columns son los nombres. enumerate nos da (0, 'AD'), (1, '% AD')...
        for col_num, value in enumerate(df.columns.values):
            val_str = str(value).upper() # Convertimos a mayúsculas para comparar
            
            # Elegimos el color según la letra
            if "AD" in val_str or ("A" in val_str and "% A" in val_str) or "A (EST.)" in val_str:
                cell_format = fmt_green
            elif "B" in val_str:
                cell_format = fmt_orange
            elif "C" in val_str:
                cell_format = fmt_red
            else:
                cell_format = fmt_header # Por defecto (ej: Total)

            # Escribimos en la fila 0, columna (col_num + 1 porque la A es el índice)
            worksheet.write(0, col_num + 1, value, cell_format)

    return output.getvalue()

# =========================================================================
# === 6. FUNCIÓN PRINCIPAL `home_page` (EL DASHBOARD) v4.0 ===
# =========================================================================
def home_page():
    
    if st.session_state.show_welcome_message:
        user_email = "Usuario"
        if hasattr(st.session_state, 'user') and st.session_state.user:
            user_name = st.session_state.user.user_metadata.get('full_name', st.session_state.user.email)
            st.toast(f"¡Bienvenido, {user_name}!", icon="👋")
        st.session_state.show_welcome_message = False

    # INICIALIZACIÓN DE VARIABLES
    if 'sesion_generada' not in st.session_state: st.session_state.sesion_generada = None
    if 'docx_bytes' not in st.session_state: st.session_state.docx_bytes = None
    if 'tema_sesion' not in st.session_state: st.session_state.tema_sesion = ""

# ENCABEZADO DASHBOARD
    # Modificamos para tener 3 columnas: Logo (1) | Título (4) | Robot (1)
    col_logo, col_titulo, col_bot = st.columns([1, 4, 1])

    with col_logo:
        try:
            # Mantenemos tu logo original
            st.image(ISOTIPO_PATH, width=120)
        except:
            st.warning("No isotipo.")
            
    with col_titulo:
        # Mantenemos tu título con el estilo degradado que ya tenías
        st.markdown('<h1 class="gradient-title-dashboard">Generador de Análisis Pedagógico</h1>', unsafe_allow_html=True)
        st.markdown("Selecciona una herramienta para comenzar.")

    with col_bot:
        # 👇 Aquí ponemos al Robot saludando a la derecha
        try:
            lottie_hello = cargar_lottie("robot_hello.json")
            st_lottie(lottie_hello, height=180, key="robot_header")
        except:
            pass

  # SIDEBAR
    st.sidebar.divider() 
    # (Aquí sigue tu código existente de Yape...)
    col_izq, col_centro, col_der = st.sidebar.columns([1, 2, 1])
    # ...
    with col_centro:
        st.image("assets/qr-yape.png") 
    
    st.sidebar.markdown("<div style='text-align: center; font-size: 0.9em;'>¡Ayúdanos a mantener la página gratuita!</div>", unsafe_allow_html=True)
    st.sidebar.divider()

    # --- 👇 NUEVO BOTÓN: RESETEAR / CARGAR NUEVO ---
    if st.sidebar.button("📂 Subir Nuevo Archivo", use_container_width=True):
        # 1. Borramos las memorias de datos
        st.session_state.df_cargado = False
        st.session_state.info_areas = None
        st.session_state.all_dataframes = None
        st.session_state.df = None
        
        # 2. Truco Pro: Borramos la memoria del widget de carga para que aparezca vacío
        if 'file_uploader' in st.session_state:
            del st.session_state['file_uploader']
            
        st.rerun()
    # -----------------------------------------------

    if st.sidebar.button("Cerrar Sesión", key="logout_sidebar_button"):
        try:
            supabase.auth.sign_out()
        except:
            pass
        st.session_state.logged_in = False
        # Verificamos si existe antes de borrar para evitar errores
        if hasattr(st.session_state, 'user'):
            del st.session_state.user
        st.rerun()

    # --- TABS PRINCIPALES (4 PESTAÑAS) ---
    tab_general, tab_estudiante, tab_asistente, tab_recursos = st.tabs([
        "📊 Análisis General", 
        "🧑‍🎓 Análisis por Estudiante", 
        "🧠 Asistente Pedagógico",
        "📂 Recursos"
    ])

    # TAB 1: ANÁLISIS
    with tab_general:
        if st.session_state.df_cargado:
            info_areas = st.session_state.info_areas
            mostrar_analisis_general(info_areas)
        else:
            st.subheader("Subir Archivo de Notas")
            st.info("Para comenzar el análisis de notas, sube tu registro de Excel aquí.")
            configurar_uploader() 

    # TAB 2: ESTUDIANTE
    with tab_estudiante:
        if st.session_state.df_cargado:
            df = st.session_state.df
            df_config = st.session_state.df_config
            info_areas = st.session_state.info_areas
            mostrar_analisis_por_estudiante(df, df_config, info_areas)
        else:
            st.header("🧑‍🎓 Análisis Individual por Estudiante")
            st.info("Esta función requiere un archivo de notas.")
            st.warning("Por favor, ve a la pestaña **'📊 Análisis General'** y sube tu archivo de Excel para activar esta vista.")

# TAB 3: ASISTENTE
    with tab_asistente:
        st.header("🧠 Asistente Pedagógico")
              
        tipo_herramienta = st.radio(
            "01. Selecciona la herramienta que deseas usar:",
            options=["Sesión de aprendizaje", "Unidad de aprendizaje", "Planificación Anual"],
            index=0, horizontal=True, key="asistente_tipo_herramienta"
        )
        st.markdown("---")

        if st.session_state.asistente_tipo_herramienta == "Sesión de aprendizaje":
            st.subheader("Generador de Sesión de Aprendizaje")
            df_gen, df_cic, df_desc_sec, df_desc_prim = cargar_datos_pedagogicos()
            
            if df_gen is None:
                st.error("Error crítico: No se pudieron cargar los estándares.")
            else:
                st.subheader("Paso 1: Selecciona el Nivel")
                niveles = df_gen['NIVEL'].dropna().unique()
                nivel_sel = st.selectbox("Nivel", options=niveles, index=None, placeholder="Elige una opción...", key="asistente_nivel_sel", label_visibility="collapsed")
                
                st.subheader("Paso 2: Selecciona el Grado")
                grados_options = []
                if st.session_state.asistente_nivel_sel:
                    grados_options = df_gen[df_gen['NIVEL'] == st.session_state.asistente_nivel_sel]['GRADO CORRESPONDIENTE'].dropna().unique()
                grado_sel = st.selectbox("Grado", options=grados_options, index=None, placeholder="Elige un Nivel primero...", disabled=(not st.session_state.asistente_nivel_sel), key="asistente_grado_sel", label_visibility="collapsed")

                st.subheader("Paso 3: Selecciona el Área")
                areas_options = []
                df_hoja_descriptor = None 
                if st.session_state.asistente_grado_sel:
                    if st.session_state.asistente_nivel_sel == "SECUNDARIA":
                        df_hoja_descriptor = df_desc_sec
                    elif st.session_state.asistente_nivel_sel == "PRIMARIA":
                        df_hoja_descriptor = df_desc_prim
                    if df_hoja_descriptor is not None:
                        areas_options = df_hoja_descriptor['Área'].dropna().unique()
                area_sel = st.selectbox("Área", options=areas_options, index=None, placeholder="Elige un Grado primero...", disabled=(not st.session_state.asistente_grado_sel), key="asistente_area_sel", label_visibility="collapsed")

                st.subheader("Paso 4: Selecciona la(s) Competencia(s)")
                competencias_options = []
                if st.session_state.asistente_area_sel and (df_hoja_descriptor is not None):
                    competencias_options = df_hoja_descriptor[
                        df_hoja_descriptor['Área'] == st.session_state.asistente_area_sel
                    ]['Competencia'].dropna().unique()
                competencias_sel = st.multiselect("Competencia(s)", options=competencias_options, placeholder="Elige un Área primero...", disabled=(not st.session_state.asistente_area_sel), key="asistente_competencias_sel", label_visibility="collapsed")
                
                form_disabled = not st.session_state.asistente_competencias_sel

                st.markdown("---")
                st.subheader("Paso 5: Contextualización (Opcional)")
                contexto_toggle = st.toggle("¿Desea contextualizar su sesión?", key="asistente_contexto", disabled=form_disabled)

                with st.form(key="session_form"):
                    if st.session_state.asistente_contexto:
                        st.info("La IA usará estos datos para generar ejemplos y situaciones relevantes.")
                        region_sel = st.text_input("Región de su I.E.", placeholder="Ej: Lambayeque", disabled=form_disabled)
                        provincia_sel = st.text_input("Provincia de su I.E.", placeholder="Ej: Chiclayo", disabled=form_disabled)
                        distrito_sel = st.text_input("Distrito de su I.E.", placeholder="Ej: Monsefú", disabled=form_disabled)
                    else:
                        region_sel = None; provincia_sel = None; distrito_sel = None
                    
                    st.markdown("---")
                    st.subheader("Paso 6: Instrucciones Adicionales (Opcional)")
                    instrucciones_sel = st.text_area("Indica un enfoque específico para la IA", placeholder="Ej: Quiero reforzar el cálculo de porcentajes...", max_chars=500, disabled=form_disabled)

                    st.markdown("---")
                    st.subheader("Paso 7: Detalles de la Sesión")
                    tema_sel = st.text_input("Escribe el tema o temática a tratar", placeholder="Ej: El sistema solar...", disabled=form_disabled)
                    tiempo_sel = st.selectbox("Selecciona la duración de la sesión", options=["90 minutos", "180 minutos"], index=None, placeholder="Elige una opción...", disabled=form_disabled)
                    
                    submitted = st.form_submit_button("Generar Sesión de Aprendizaje", disabled=form_disabled)
                    
                    if submitted:
                        if not tema_sel or not tiempo_sel:
                            st.error("Por favor, completa los campos del Paso 7.")
                            st.session_state.sesion_generada = None
                            st.session_state.docx_bytes = None
                        else:
                            with st.spinner("🤖 Generando tu sesión de aprendizaje..."):
                                try:
                                    nivel = st.session_state.asistente_nivel_sel
                                    grado = st.session_state.asistente_grado_sel
                                    area = st.session_state.asistente_area_sel
                                    competencias = st.session_state.asistente_competencias_sel 
                                    tema = tema_sel
                                    tiempo = tiempo_sel
                                    
                                    ciclo_float = df_cic[df_cic['grados que corresponde'] == grado]['ciclo'].iloc[0]
                                    ciclo_encontrado = int(ciclo_float) 
                                    datos_filtrados = df_hoja_descriptor[(df_hoja_descriptor['Área'] == area) & (df_hoja_descriptor['Competencia'].isin(competencias))]
                                    capacidades_lista = datos_filtrados['capacidad'].dropna().unique().tolist()
                                    columna_estandar_correcta = "DESCRIPCIÓN DE LOS NIVELES DEL DESARROLLO DE LA COMPETENCIA"
                                    estandares_lista = datos_filtrados[columna_estandar_correcta].dropna().unique().tolist()
                                    estandar_texto_completo = "\n\n".join(estandares_lista)

                                    sesion_generada = pedagogical_assistant.generar_sesion_aprendizaje(
                                        nivel=nivel, grado=grado, ciclo=str(ciclo_encontrado), area=area,
                                        competencias_lista=competencias, capacidades_lista=capacidades_lista,
                                        estandar_texto=estandar_texto_completo, tematica=tema, tiempo=tiempo,
                                        region=region_sel, provincia=provincia_sel, distrito=distrito_sel,
                                        instrucciones_docente=instrucciones_sel 
                                    )
                                    docx_bytes = pedagogical_assistant.generar_docx_sesion(sesion_markdown_text=sesion_generada, area_docente=area)
                                    
                                    st.session_state.sesion_generada = sesion_generada
                                    st.session_state.docx_bytes = docx_bytes
                                    st.session_state.tema_sesion = tema_sel
                                    st.success("¡Sesión generada!")

                                except Exception as e:
                                    st.error(f"Error: {e}")
                                    st.session_state.sesion_generada = None
                
# MOSTRAR RESULTADOS
        if st.session_state.sesion_generada:
            st.markdown("---")
            st.subheader("Resultado")
            st.markdown(st.session_state.sesion_generada)
            
            st.success("¡Sesión generada con éxito!")
            
            # 🛡️ ZONA DE DESCARGA (CORREGIDA)
            # Verificamos si los bytes del archivo existen en la memoria permanente
            if st.session_state.get('docx_bytes'):
                
                st.download_button(
                    label="📄 Descargar Sesión en Word",
                    data=st.session_state.docx_bytes, # <--- ¡AQUÍ ESTABA LA CLAVE!
                    file_name="Sesion_Aprendizaje.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ El archivo expiró. Por favor genera la sesión de nuevo.")

    # 👇 ESTOS ELIF DEBEN IR ALINEADOS A LA IZQUIERDA (AL MISMO NIVEL QUE EL IF PRINCIPAL)
        elif st.session_state.asistente_tipo_herramienta == "Unidad de aprendizaje":
            st.info("Función de Unidades de Aprendizaje (Próximamente).")
        
        elif st.session_state.asistente_tipo_herramienta == "Planificación Anual":
            st.info("Función de Planificación Anual (Próximamente).")

    # --- TAB 4: RECURSOS (¡NUEVA!) ---
    with tab_recursos:
        st.header("📂 Banco de Recursos Pedagógicos")
        st.markdown("Descarga formatos, plantillas y guías útiles para tu labor docente.")
        st.divider()

        col_formatos, col_guias = st.columns(2)

        with col_formatos:
            st.subheader("📝 Formatos Editables")
            st.info("Plantillas en Word y Excel listas para usar.")
            
           # RECURSO 1: SECUNDARIA (Excel)
            # 1. Agregamos "recursos/" antes del nombre
            ruta_archivo_1 = "recursos/Registro automatizado nivel secundario.xlsm" 
            
            if os.path.exists(ruta_archivo_1):
                with open(ruta_archivo_1, "rb") as file:
                    st.download_button(
                        label="📥 Descargar Registro Automatizado - Secundaria (Excel)", # 2. Corregimos la etiqueta
                        data=file,
                        file_name="Registro_Secundaria.xlsm", # 3. Nombre limpio para la descarga
                        # 4. Tipo MIME correcto para archivos Excel con macros (.xlsm)
                        mime="application/vnd.ms-excel.sheet.macroEnabled.12", 
                        use_container_width=True
                    )
            else:
                # Esto te ayudará a ver si el nombre está mal escrito
                st.caption(f"❌ Archivo no encontrado en: {ruta_archivo_1}")

            st.write("")
            
   # RECURSO 2: PRIMARIA (Excel)
            # CAMBIO IMPORTANTE: Usamos 'ruta_archivo_2' para no mezclar con el anterior
            ruta_archivo_2 = "recursos/Registro automatizado nivel primario.xlsm" 
            
            if os.path.exists(ruta_archivo_2):
                with open(ruta_archivo_2, "rb") as file:
                    st.download_button(
                        label="📥 Descargar Registro Automatizado - Primaria (Excel)",
                        data=file,
                        file_name="Registro_Primaria.xlsm",
                        mime="application/vnd.ms-excel.sheet.macroEnabled.12", 
                        use_container_width=True
                    )
            else:
                st.caption(f"❌ Archivo no encontrado en: {ruta_archivo_2}")

            st.write("")
            
            # RECURSO 3
            ruta_archivo_3 = "recursos/calendario_2025.pdf" 
            if os.path.exists(ruta_archivo_3):
                with open(ruta_archivo_3, "rb") as file:
                    st.download_button("📥 Descargar Calendario Cívico (PDF)", file, "Calendario_Civico_2025.pdf", "application/pdf", use_container_width=True)
            else:
                st.caption("❌ Archivo 'calendario_2025.pdf' no disponible.")

# =========================================================================
# === 7. EJECUCIÓN PRINCIPAL ===
# =========================================================================
query_params = st.query_params
auth_code = query_params.get("code")

if auth_code and not st.session_state.logged_in:
    try:
        session_data = supabase.auth.exchange_code_for_session(auth_code)
        if session_data.session:
            st.session_state.logged_in = True
            st.session_state.user = session_data.session.user
            st.session_state.show_welcome_message = True
            st.query_params.clear() 
            st.rerun()
    except Exception:
        st.query_params.clear() 
        pass 
    
if not st.session_state.logged_in:
    login_page()
else:
    home_page()






































