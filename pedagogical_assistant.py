import streamlit as st
import os
import pandas as pd
import io
import re 
import random
import string
import json
from google import genai
# Importamos la clase de Error específica para capturarla
from google.genai.errors import APIError 
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
# Necesitamos 'parse' para la nueva función de Word
from docx.text.paragraph import Paragraph
from docx.table import _Cell

# --- 👇 NUEVOS IMPORTS NECESARIOS PARA EL COLOR DE FONDO 👇 ---
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
# --------------------------------------------------------------

# =========================================================================
# === 1. CONFIGURACIÓN GLOBAL DE LA IA ===
# =========================================================================

try:
    gemini_key = st.secrets['gemini']['api_key']
    client = genai.Client(api_key=gemini_key)
except KeyError:
    st.error("Error de Configuración: No se encontró la clave de Gemini en st.secrets.")
    client = None
except Exception as e:
    st.error(f"Error al inicializar el cliente de Gemini: {e}")
    client = None

# =========================================================================
# === I. FUNCIÓN DE PROPUESTAS (Pestaña 1) ===
# =========================================================================

def generate_ai_suggestions(critical_comp_info):
    """
    Genera un plan de acción (propuestas de mejora) usando la IA.
    Usa el modelo 'pro' para alta consistencia de formato.
    """
    
    if client is None:
        return "⚠️ **Error de Configuración de IA:** El cliente de Gemini no se pudo inicializar."
        
    # Extraemos las variables dinámicas
    grado = critical_comp_info['grado']
    nivel = critical_comp_info['nivel']
    area = critical_comp_info['area']
    competencia = critical_comp_info['nombre']
    analisis = critical_comp_info['analisis'] 
    
    prompt = f"""
    Quiero que elabores un **cuadro claro y completo** con acciones, indicadores y evidencias de mejora, dirigido a un docente de **{area}** de **{grado}** de {nivel}.

    El enfoque debe estar orientado a mejorar el desempeño de los estudiantes que presentan dificultades, basado en el siguiente diagnóstico:
    **Diagnóstico:** {analisis}
    **Competencia a mejorar:** "{competencia}"

    El cuadro debe contener **5 acciones concretas** que el docente puede implementar. Por cada acción, debes incluir:
    1.  **Indicadores de mejora:** (Cómo se evidencia el progreso del estudiante o de la práctica docente).
    2.  **Evidencias esperadas:** (Documentos, actitudes, producciones u observaciones visibles que demuestran ese progreso).

    **REGLAS DE FORMATO ESTRICTAS:**
    1.  Formatea la respuesta como una **tabla Markdown** (usando |, ---, etc.).
    2.  Las columnas deben ser: **Acción Concreta**, **Indicadores de Mejora**, y **Evidencias Esperadas**.
    3.  **NO** incluyas **ningún** código HTML, CSS, o etiquetas <div>, <span> o <style>.
    4.  No añadas introducciones o conclusiones fuera de la tabla. La respuesta debe ser *solo* la tabla.
    """
    
    try:
        response = client.models.generate_content(
            model='models/gemini-2.5-flash-preview-09-2025', 
            contents=prompt,
        )
        return response.text
    except APIError as e: 
        return f"❌ **Error al contactar la IA:** Se produjo un error en la API de Google (Código: {e}). Revisa tu clave y la cuota de uso."
    except Exception as e:
        return f"❌ **Error desconocido:** {e}"


# =========================================================================
# === II-A. FUNCIÓN DE EXPORTACIÓN A WORD (Propuestas) ===
# =========================================================================
def generate_docx_report(analisis_results, sheet_name, selected_comp_limpio, ai_report_text):
    document = Document()
    result = analisis_results[sheet_name]
    general_data = result.get('generalidades', {})
    grado = general_data.get('grado', 'Desconocido')
    nivel = general_data.get('nivel', 'Desconocido')
    
    document.add_heading(f'INFORME DE PROPUESTAS PEDAGÓGICAS', 0)
    document.add_heading('Datos de Contexto y Diagnóstico', level=1)
    document.add_paragraph(f"Nivel/Grado: {nivel} / {grado}")
    document.add_paragraph(f"Área Analizada: {sheet_name}")
    
    p_comp = document.add_paragraph()
    p_comp.add_run(f"Competencia a Abordar: ").bold = True
    p_comp.add_run(selected_comp_limpio)
    
    document.add_heading('Propuestas de Intervención (Generadas por IA)', level=1)
    
    def process_markdown_to_runs(paragraph, text):
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                paragraph.add_run(part[2:-2]).bold = True
            elif part.startswith('*') and part.endswith('*'):
                paragraph.add_run(part[1:-1]).italic = True
            else:
                paragraph.add_run(part)

    lines = ai_report_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "propuestas de intervención didáctica" in line.lower() or "propuestas de intervención (generadas por ia)" in line.lower():
            continue
        if line.startswith('###'):
            document.add_heading(re.sub(r'^###\s*', '', line).strip(), level=2)
        elif line.startswith('##'):
            document.add_heading(re.sub(r'^##\s*', '', line).strip(), level=1)
        elif line.startswith('#'):
            document.add_heading(re.sub(r'^#s*', '', line).strip(), level=1)
        elif re.match(r'^\d+\.', line):
            paragraph = document.add_paragraph(style='List Number')
            cleaned_line = re.sub(r'^\d+\.\s*', '', line).strip()
            process_markdown_to_runs(paragraph, cleaned_line)
        elif line.startswith('*'):
            paragraph = document.add_paragraph(style='List Bullet')
            cleaned_line = re.sub(r'^\*\s*', '', line).strip()
            process_markdown_to_runs(paragraph, cleaned_line)
        else:
            if line: 
                paragraph = document.add_paragraph()
                process_markdown_to_runs(paragraph, line)
                
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# =========================================================================
# === II-B. EXPORTACIÓN A WORD INTELIGENTE (Sesión) - v4.0 COLOR ===
# =========================================================================
def generar_docx_sesion(sesion_markdown_text, area_docente):
    """
    Convierte la sesión a Word con:
    - Filtro de inicio estricto.
    - Tabla de competencias con ENCABEZADOS DE COLOR.
    - Limpieza y formato de texto reparados.
    """
    document = Document()
    
    # --- ESTILOS BÁSICOS ---
    style = document.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    # --- FUNCIÓN TRUCO PARA PINTAR CELDAS (XML) ---
    def set_cell_shading(cell, fill_color):
        """
        Pinta el fondo de una celda. 
        fill_color: Código Hexadecimal sin # (ej: 'E7F3FF').
        """
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill_color)
        tcPr.append(shd)

    # --- HELPERS DE TEXTO ---
    def clean_markdown_symbols(text):
        return text.replace('>', '').strip()

    def clean_asterisks(text):
        return text.replace('**', '').replace('*', '').strip()

    def process_formatted_text(paragraph, text):
        text = clean_markdown_symbols(text)
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                clean_part = part[2:-2]
                run = paragraph.add_run(clean_part)
                run.bold = True
            else:
                paragraph.add_run(part)

    def add_bullet(paragraph, text, style='List Bullet'):
        clean_text = re.sub(r'^[\*\-\+]\s*', '', text)
        paragraph.style = style
        process_formatted_text(paragraph, clean_text)

    lines = sesion_markdown_text.split('\n')
    
    # --- VARIABLES DE ESTADO ---
    printing_started = False 
    in_competencies_section = False
    table = None
    curr_comp = ""
    curr_caps = []
    curr_crits = []
    capture_mode = 0 

    def flush_row(tbl, c, caps, crits):
        if not c and not caps and not crits: return
        row = tbl.add_row()
        row.cells[0].text = clean_asterisks(c)
        if caps:
            row.cells[1].paragraphs[0].text = "" 
            for cap in caps:
                p = row.cells[1].add_paragraph()
                add_bullet(p, cap)
        if crits:
            row.cells[2].paragraphs[0].text = ""
            for crit in crits:
                p = row.cells[2].add_paragraph()
                add_bullet(p, crit)

    # --- BUCLE PRINCIPAL ---
    for line in lines:
        line = line.strip()
        if not line: continue

        if line.upper().startswith("### SESIÓN DE APRENDIZAJE") and not printing_started:
            printing_started = True
            p = document.add_heading('SESIÓN DE APRENDIZAJE', level=0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue 
        
        if not printing_started: continue 

        if re.match(r'^(\*\*)?(I|II|III|IV|V|VI|VII)\.', line):
            if in_competencies_section and table:
                flush_row(table, curr_comp, curr_caps, curr_crits)
                curr_comp, curr_caps, curr_crits = "", [], []
                in_competencies_section = False

            clean_title = line.replace('**', '').strip()
            document.add_heading(clean_title, level=1)

            if "COMPETENCIAS" in line.upper():
                in_competencies_section = True
                table = document.add_table(rows=1, cols=3)
                table.style = 'Table Grid'
                
                # --- CONFIGURACIÓN DE ENCABEZADOS CON COLOR ---
                hdr_row = table.rows[0]
                hdr = hdr_row.cells
                
                headers = ['COMPETENCIA', 'CAPACIDAD', 'CRITERIOS DE EVALUACIÓN']
                # Color Azul Suave (Hex: D9EAD3 es verde suave, usaremos E7F3FF para azul suave)
                color_header = "E7F3FF" 
                
                for i, text in enumerate(headers):
                    hdr[i].text = text
                    # ¡Aquí aplicamos el color!
                    set_cell_shading(hdr[i], color_header) 
                    # Ponemos negrita
                    hdr[i].paragraphs[0].runs[0].bold = True
                # ---------------------------------------------
            
            continue

        # --- LÓGICA DE TABLA (INTACTA) ---
        if in_competencies_section:
            if "---" in line:
                flush_row(table, curr_comp, curr_caps, curr_crits)
                curr_comp, curr_caps, curr_crits = "", [], []
                capture_mode = 0
                continue
            if "Competencia:" in line: 
                if curr_comp: 
                     flush_row(table, curr_comp, curr_caps, curr_crits)
                     curr_caps, curr_crits = [], []
                text_parts = line.split("ompetencia:") 
                if len(text_parts) > 1:
                    curr_comp = text_parts[1].replace('**', '').strip()
                capture_mode = 0
            elif "Capacidades:" in line: capture_mode = 1
            elif "Criterios" in line and "Evaluación" in line: capture_mode = 2
            elif line.startswith('-') or line.startswith('*'):
                content = re.sub(r'^[\*\-]\s*', '', line).strip()
                if capture_mode == 1: curr_caps.append(content)
                elif capture_mode == 2: curr_crits.append(content)
            continue 

        # --- CONTENIDO NORMAL ---
        if line.startswith("###"):
            clean_h = line.replace('###', '').strip()
            document.add_heading(clean_h, level=2)
        elif line.startswith('**') and line.endswith('**') and ":" in line:
             p = document.add_paragraph()
             clean_line = line.replace('**', '').strip()
             run = p.add_run(clean_line)
             run.bold = True
        elif line.startswith('* ') or line.startswith('- '):
            p = document.add_paragraph()
            add_bullet(p, line, style='List Bullet')
        elif line.startswith('>'):
            clean_line = line.replace('>', '').strip()
            if clean_line.startswith('*') or clean_line.startswith('-'):
                p = document.add_paragraph()
                add_bullet(p, clean_line)
            else:
                p = document.add_paragraph()
                process_formatted_text(p, clean_line)
        elif re.match(r'^\d+\.', line):
            p = document.add_paragraph(style='List Number')
            clean_text = re.sub(r'^\d+\.\s*', '', line)
            process_formatted_text(p, clean_text)
        elif line.startswith('_'):
            p = document.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            p = document.add_paragraph()
            process_formatted_text(p, line)

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# =========================================================================
# === III. FUNCIÓN PRINCIPAL LLAMADA DESDE APP.PY (Propuestas) ===
# =========================================================================
def generate_suggestions(analisis_results, selected_sheet_name, selected_comp_limpio):
    sheet_name = selected_sheet_name
    result = analisis_results[sheet_name]
    
    st.markdown("### 📋 Informe de Intervención Pedagógica")

    if 'error' in result:
        st.error(f"No se puede generar el informe debido al error en el análisis de la hoja '{sheet_name}'.")
        return "Error en el análisis."

    target_comp_data = None
    for original_name, comp_data in result['competencias'].items():
        if comp_data['nombre_limpio'] == selected_comp_limpio:
            target_comp_data = comp_data
            break
            
    if not target_comp_data:
        st.error(f"Error: No se encontró la competencia '{selected_comp_limpio}' en los datos de análisis.")
        return "Error: Competencia no encontrada."

    counts = target_comp_data['conteo_niveles']
    total = target_comp_data['total_evaluados']
    
    if total == 0:
        st.info(f"La competencia '{selected_comp_limpio}' no tiene estudiantes evaluados.")
        return "Error: Sin evaluados."
        
    c_count = counts.get('C', 0)
    b_count = counts.get('B', 0)
    c_percentage = (c_count / total) * 100
    
    critical_comp_info = {
        'area': sheet_name,
        'nombre': selected_comp_limpio,
        'analisis': f"El {c_percentage:.1f}% de los estudiantes ({c_count} estudiantes) se encuentra en el Nivel C. El {((b_count+c_count)/total)*100:.1f}% ({b_count+c_count} estudiantes) está en nivel de inicio (B o C).",
        'grado': result['generalidades'].get('grado'),
        'nivel': result['generalidades'].get('nivel')
    }

    st.markdown(f"**Diagnóstico:** El área de **{critical_comp_info['area']}** en **{critical_comp_info['grado']}** requiere atención especial en la competencia:")
    st.markdown(f"#### ⚠️ {critical_comp_info['nombre']}")
    st.markdown(f"**Análisis de Dificultad:** {critical_comp_info['analisis']}")
    st.markdown("---")

    with st.spinner("🧠 Generando propuestas pedagógicas con Inteligencia Artificial..."):
        ai_response_text = generate_ai_suggestions(critical_comp_info)
        return ai_response_text 

# =========================================================================
# === IV. FUNCIÓN DE GENERACIÓN DE SESIÓN (Pestaña 3) ===
# === (Versión ORIGINAL ESTABLE) ===
# =========================================================================

def generar_sesion_aprendizaje(nivel, grado, ciclo, area, competencias_lista, capacidades_lista, estandar_texto, tematica, tiempo, 
                                region=None, provincia=None, distrito=None, instrucciones_docente=None):
    """
    Genera una sesión de aprendizaje completa usando la IA.
    Incluye SELECTOR METODOLÓGICO y MANDATO DE ALTA DEMANDA COGNITIVA.
    """
    
    if client is None:
        return "⚠️ **Error de Configuración de IA:** El cliente de Gemini no se pudo inicializar."

    # 1. Convertir listas a texto formateado
    competencias_str = "\n".join(f"- {comp}" for comp in competencias_lista)
    capacidades_str = "\n".join(f"- {cap}" for cap in capacidades_lista)

    # --- CONTEXTO GEOGRÁFICO ---
    contexto_str = ""
    if region and region.strip(): 
        contexto_str = f"""
## CONTEXTO GEOGRÁFICO (Opcional)
- **Región:** {region}
- **Provincia:** {provincia}
- **Distrito:** {distrito}
**REGLA DE CONTEXTUALIZACIÓN:** DEBES usar estos datos para generar ejemplos relevantes.
"""
    
    # --- INSTRUCCIONES ADICIONALES ---
    instrucciones_str = ""
    if instrucciones_docente and instrucciones_docente.strip():
        instrucciones_str = f"""
## INSTRUCCIONES ADICIONALES DEL DOCENTE
- {instrucciones_docente}
**REGLA DE PRIORIDAD:** ¡Esta es la instrucción más importante! Modifica la sesión para cumplir esto.
"""

    # --- MENÚ DE METODOLOGÍAS ACTIVAS (NUEVO) ---
    menu_metodologias = """
    1. Aprendizaje Basado en Problemas (ABP)
    2. Aprendizaje Basado en Indagación (Indagación Científica)
    3. Aprendizaje Colaborativo / Cooperativo
    4. Gamificación (Uso de mecánicas de juego)
    5. Estudio de Casos
    6. Aula Invertida (Flipped Classroom)
    """

    # 2. Construir el Mega-Prompt con ESTRATEGIA PEDAGÓGICA
    prompt = f"""
    Actúa como un docente experto y diseñador curricular en el sistema educativo peruano.
    
    ## ESTRATEGIA PEDAGÓGICA (SELECTOR METODOLÓGICO):
    Antes de generar la sesión, ANALIZA el Grado ({grado}), el Área ({area}) y el Tema ({tematica}).
    Basado en este análisis, **ELIGE** la metodología más apropiada de la siguiente lista:
    {menu_metodologias}
    
    ## MANDATO DE ALTA DEMANDA COGNITIVA:
    En la sección de **'DESARROLLO'**, es **OBLIGATORIO** incluir una actividad explícita que promueva:
    - El Razonamiento Complejo.
    - La Creatividad.
    - O el Pensamiento Crítico.
    
    Evita a toda costa que los estudiantes sean pasivos. La sesión debe centrarse en lo que el estudiante HACE, no solo en lo que el docente explica.

    ## DATOS DE ENTRADA:
    - **Nivel:** {nivel}
    - **Grado:** {grado}
    - **Ciclo:** {ciclo}
    - **Área:** {area}
    - **Tema:** {tematica}
    - **Duración:** {tiempo}

    {contexto_str} 

    ## RECURSOS PEDAGÓGICOS:
    **Competencia(s):**
    {competencias_str}
    **Capacidad(es):**
    {capacidades_str}
    **Estándar(es):**
    "{estandar_texto}"

    {instrucciones_str}

    ## PLANTILLA DE SALIDA (Formato Requerido):
    Genera la sesión usando este formato Markdown exacto.

    ### SESIÓN DE APRENDIZAJE – N° 

    **I. DATOS GENERALES:**
    * **Título:** [Genera un título creativo para la sesión]
    * **Unidad de Aprendizaje:** * **Duración:** {tiempo}
    * **Fecha:** * **Ciclo:** {ciclo}
    * **Grado:** {grado}
    * **Metodología:** [¡IMPORTANTE! Escribe aquí la metodología que elegiste del menú]
    * **Sección:** * **Docente:** **II. PROPÓSITO DE LA SESIÓN:**
    [Genera el propósito: Verbo + tema + estrategia + finalidad]

    **III. COMPETENCIAS Y CAPACIDADES:**
    
    **REGLA DE FORMATO:**
    - **Competencia: [Nombre]**
    - **Capacidades:** (Lista con guiones `-`)
    - **Criterios de Evaluación:** (Lista con guiones `-`. Genera 3-4 criterios adaptados estrictamente al grado {grado} y al tema).
    --- (Separador)

    **DATOS:**
    - **Competencia(s):** {competencias_str}
    - **Capacidad(es):** {capacidades_str}

    **IV. ENFOQUE TRANSVERSAL:**
    (Espacio vacío)
    
    **V. SECUENCIA DIDÁCTICA:**

    ### INICIO
    (Tiempo estimado: [Corto])
    **Motivación:** [Actividad corta y motivadora]
    **Saberes previos:** [Preguntas]
    **Conflicto cognitivo:** [Pregunta retadora]
    **Presentación del propósito:** [El docente presenta propósito y criterios]

    ### DESARROLLO
    (Tiempo estimado: [Largo])
    
    **Gestión y acompañamiento:** [Describe la secuencia didáctica paso a paso usando la **Metodología** elegida.]
    
    **ACTIVIDAD DE ALTA DEMANDA COGNITIVA:**
    [Describe aquí detalladamente el reto, problema, debate o creación que realizarán los estudiantes para desarrollar su pensamiento crítico/creativo.]

    ### CIERRE
    (Tiempo estimado: [Corto])
    **Evaluación/Transferencia:** [Actividad de cierre]
    **Metacognición:** [Preguntas de reflexión]
    
    **VI. MATERIALES O RECURSOS:**
    * [Lista de materiales]

    **VII. FIRMAS:**
    ___
    DIRECTOR
    ___
    DOCENTE
    """
    
    try:
        # 1. Intentar con modelo flash-preview-09-2025
        response = client.models.generate_content(
            model='models/gemini-2.5-flash-preview-09-2025',
            contents=prompt
        )
        return response.text
    
    except APIError as e: 
        # 2. Reintento con Flash si falla
        if "503" in str(e) or "overloaded" in str(e).lower():
            try:
                response_flash = client.models.generate_content(
                    model='models/gemini-2.5-flash',
                    contents=prompt
                )
                return response_flash.text
            except Exception as e_flash:
                return f"Error al contactar la IA (reintento fallido): {e_flash}"
        else:
            return f"Error al contactar la IA (APIError): {e}"
    except Exception as e:
        return f"Error inesperado: {e}"

# =========================================================================
# === V. GENERADOR DE INFORME DEL ESTUDIANTE (Word con Colores) ===
# =========================================================================
def generar_reporte_estudiante(nombre_estudiante, total_conteo, desglose_areas):
    """
    Genera un informe individual en Word con formato semáforo (colores).
    """
    document = Document()
    
    # --- ESTILOS ---
    style = document.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    # --- FUNCIÓN INTERNA PARA COLOR (Para pintar celdas en Word) ---
    def set_cell_shading(cell, fill_color):
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill_color)
        tcPr.append(shd)

    # 1. ENCABEZADO
    # Creamos el título pero accedemos a su "run" (el texto) para cambiarle el tamaño
    h1 = document.add_heading('INFORME DE PROGRESO DEL APRENDIZAJE', 0)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # AJUSTE DE TAMAÑO (Arial 18)
    run = h1.runs[0]
    run.font.name = 'Arial'
    run.font.size = Pt(18)  # <--- AQUÍ ESTÁ EL EQUIVALENTE A ARIAL 18
    run.font.color.rgb = RGBColor(0, 0, 0) # Aseguramos color negro
    
    document.add_paragraph(f"Estudiante: {nombre_estudiante}")
    document.add_paragraph("Fecha de emisión: _______________________")
    document.add_paragraph("")

    # 2. SEMÁFORO ACADÉMICO (Tabla de Resumen)
    document.add_heading('1. Resumen de Logros (Semáforo)', level=1)
    
    table = document.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    
    # Encabezados
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'NIVEL DE LOGRO'
    hdr_cells[1].text = 'CANTIDAD DE ÁREAS'
    for cell in hdr_cells: 
        cell.paragraphs[0].runs[0].bold = True
        set_cell_shading(cell, "D9D9D9") # Gris claro para encabezado

    # Datos del semáforo
    data = [
        ("LOGRO DESTACADO (AD)", total_conteo['AD'], "C6EFCE"), # Verde Claro
        ("LOGRO ESPERADO (A)", total_conteo['A'], "E7F3FF"),   # Azul Claro
        ("EN PROCESO (B)", total_conteo['B'], "FFEB9C"),       # Amarillo
        ("EN INICIO (C)", total_conteo['C'], "FFC7CE")         # Rojo Claro
    ]

    for nivel, cantidad, color_hex in data:
        row_cells = table.add_row().cells
        row_cells[0].text = nivel
        row_cells[1].text = str(cantidad)
        
        # Pintamos la celda del nivel
        set_cell_shading(row_cells[0], color_hex)
        row_cells[0].paragraphs[0].runs[0].bold = True
        
        # Centramos la cantidad
        row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.add_paragraph("")

    # 3. DETALLE DE ÁREAS CRÍTICAS
    if total_conteo['B'] > 0 or total_conteo['C'] > 0:
        document.add_heading('2. Áreas que requieren atención', level=1)
        
        if total_conteo['C'] > 0:
            p = document.add_paragraph()
            run = p.add_run("🛑 EN INICIO (C) - Requiere Recuperación:")
            run.bold = True
            run.font.color.rgb = RGBColor(200, 0, 0) # Rojo oscuro
            
            for area_txt in desglose_areas['C']:
                document.add_paragraph(f"   • {area_txt}", style='List Bullet')
        
        if total_conteo['B'] > 0:
            p = document.add_paragraph()
            run = p.add_run("⚠️ EN PROCESO (B) - Requiere Refuerzo:")
            run.bold = True
            run.font.color.rgb = RGBColor(200, 150, 0) # Naranja oscuro
            
            for area_txt in desglose_areas['B']:
                document.add_paragraph(f"   • {area_txt}", style='List Bullet')

    document.add_paragraph("")

    # 4. RECOMENDACIONES PEDAGÓGICAS (Automáticas)
    document.add_heading('3. Recomendaciones y Compromisos', level=1)
    
    recomendacion = ""
    if total_conteo['C'] > 0:
        recomendacion = "El estudiante requiere un mayor acompañamiento para consolidar los aprendizajes en las áreas señaladas. Se sugiere reforzar los hábitos de estudio en casa y mantener comunicación constante con los docentes para asegurar su proceso de aprendizaje."
    elif total_conteo['B'] > 0:
        recomendacion = "Va por buen camino. Sugerimos motivar al estudiante a participar más activamente y revisar juntos sus avances semanales para que logre alcanzar el nivel de logro esperado en el corto plazo."
    else:
        recomendacion = "¡Felicitaciones! El estudiante demuestra un alto nivel de compromiso y logro de competencias. Se sugiere mantener la motivación, leer libros de interés y explorar nuevos retos académicos."
    
    document.add_paragraph(recomendacion)
    document.add_paragraph("")
    document.add_paragraph("")

    # 5. FIRMAS
    table_firmas = document.add_table(rows=1, cols=2)
    f_cells = table_firmas.rows[0].cells
    
    p1 = f_cells[0].paragraphs[0]
    p1.add_run("_________________________").bold = True
    p1.add_run("\nAPODERADO(A)")
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p2 = f_cells[1].paragraphs[0]
    p2.add_run("_________________________").bold = True
    p2.add_run("\nDOCENTE / TUTOR")
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Guardar en memoria
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# =========================================================================
# === VI. GENERADOR DE ESTRUCTURA PARA PPT (Versión 7 Slides + IMÁGENES) ===
# =========================================================================

def generar_estructura_ppt(sesion_texto):
    """
    Toma el texto completo de la sesión y usa IA para extraer
    el contenido resumido Y sugerir imágenes para 7 diapositivas.
    """
    # Verificamos si el cliente existe (asegurate que 'client' esté definido al inicio del archivo)
    # Si 'client' da error, cámbialo por la variable global que uses, ej: client
    if 'client' not in globals() and 'client' not in locals():
         return None

    # Prompt MEJORADO: Ahora solicita descripciones visuales
    prompt = f"""
    Actúa como un diseñador de presentaciones pedagógicas experto.
    Tu tarea es EXTRAER el contenido de la sesión y SUGERIR UNA IMAGEN SIMPLE para cada diapositiva.

    TEXTO DE LA SESIÓN:
    {sesion_texto}

    REGLAS DE SALIDA (ESTRICTO JSON):
    Devuelve SOLO un objeto JSON con esta estructura exacta:
    
    {{
      "slide_1": {{ 
          "titulo": "Título de la Sesión", 
          "subtitulo": "Grado, Sección y Área",
          "descripcion_imagen": "Professional and abstract background related to the main topic (e.g., 'math symbols background', 'science DNA particles', 'history ancient ruins')." 
      }},
      "slide_2": {{ 
          "titulo": "Propósito de la Sesión", 
          "contenido": "COPIA TEXTUALMENTE el párrafo del apartado 'II. PROPÓSITO DE LA SESIÓN'.",
          "descripcion_imagen": "Student achieving a goal or a person pointing to a successful target (English)."
      }},
      "slide_3": {{ 
          "titulo": "Motivación Inicial", 
          "contenido": "Extrae la actividad de motivación o la pregunta del conflicto cognitivo.",
          "descripcion_imagen": "Image illustrating the initial motivation or problem (English, e.g., 'students brainstorming', 'question mark over child')."
      }},
      "slide_4": {{ 
          "titulo": "Desarrollo y Gestión", 
          "puntos": ["Actividad principal 1", "Actividad principal 2", "Reto cognitivo"],
          "descripcion_imagen": "Students actively engaged in the main learning activity (English, e.g., 'students collaborating', 'teacher guiding')."
      }},
      "slide_5": {{ 
          "titulo": "Criterios de Evaluación", 
          "puntos": ["Criterio 1", "Criterio 2", "Criterio 3"],
          "descripcion_imagen": "Icon or image related to a checklist, rubric, or successful evaluation (English)."
      }},
      "slide_6": {{ 
          "titulo": "Cierre de la Sesión", 
          "contenido": "Resumen de la actividad de cierre o conclusiones.",
          "descripcion_imagen": "Happy students finishing a class or concept of conclusion/success (English)."
      }},
      "slide_7": {{ 
          "titulo": "Metacognición", 
          "contenido": "Extrae las preguntas de reflexión.",
          "descripcion_imagen": "Person thinking, lightbulb idea, or brain concept (English)."
      }}
    }}
    
    Reglas de Contenido:
    1. Fidelidad: El Propósito y los Criterios deben ser idénticos a la sesión.
    2. Brevedad: Resume los puntos largos (máx 30 palabras por slide).
    3. Imágenes: Las descripciones deben ser en INGLÉS, CORTAS y DIRECTAS.
    """

    try:
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return response.text
    except Exception as e:
        return None


# =========================================================================
# === VII. GENERADOR DE TRIVIA (GAMIFICACIÓN) - VERSIÓN DINÁMICA ===
# =========================================================================

def generar_trivia_juego(tema, grado, area, cantidad):
    """
    Genera preguntas de selección múltiple en formato JSON.
    Cantidad ajustable por el usuario (1-10).
    """
    if client is None:
        return None

    prompt = f"""
    Actúa como un diseñador de videojuegos educativos.
    Crea un set de **{cantidad} PREGUNTAS DE TRIVIA** divertidas y desafiantes sobre el tema: "{tema}" para estudiantes de {grado} ({area}).

    REGLAS DE FORMATO (JSON ESTRICTO):
    Devuelve SOLO un array JSON (lista de objetos) con esta estructura exacta:
    [
        {{
            "pregunta": "¿Texto de la pregunta?",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "respuesta_correcta": "Opción A",
            "explicacion": "Breve explicación de por qué es la correcta."
        }},
        ... (repetir {cantidad} veces)
    ]

    REGLAS DE CONTENIDO:
    1. Las opciones deben ser plausibles.
    2. La "respuesta_correcta" debe coincidir EXACTAMENTE con una de las "opciones".
    3. Lenguaje adecuado para {grado}.
    """

    try:
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return response.text
    except Exception as e:
        return None


# =========================================================================
# === VIII. MOTOR DE PUPILETRAS (LOGICA MIXTA: IA + ALGORITMO) ===
# =========================================================================

def generar_palabras_pupiletras(tema, grado, cantidad):
    """
    Paso 1: La IA genera la lista de palabras limpia.
    """
    if client is None:
        return None

    prompt = f"""
    Actúa como experto en didáctica. Genera una lista de {cantidad} palabras clave (sustantivos o verbos) sobre el tema: "{tema}" para estudiantes de {grado}.
    
    REGLAS OBLIGATORIAS:
    1. Las palabras deben estar en MAYÚSCULAS.
    2. SIN TILDES (convierte Á->A, É->E, etc).
    3. SIN ESPACIOS (ej: "SISTEMASOLAR" en vez de "SISTEMA SOLAR").
    4. SIN Ñ (cámbiala por N).
    5. Longitud máxima por palabra: 12 letras.
    
    FORMATO JSON:
    Devuelve SOLO una lista simple de strings:
    ["PALABRAUNO", "PALABRADOS", ...]
    """

    try:
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    except Exception as e:
        return []

def crear_grid_pupiletras(palabras, filas=12, columnas=12):
    """
    Paso 2: Algoritmo Python para colocar las palabras en una matriz 12x12.
    Retorna: (grid, palabras_colocadas)
    """
    # 1. Crear grilla vacía
    grid = [[' ' for _ in range(columnas)] for _ in range(filas)]
    palabras_colocadas = []
    
    # Direcciones: (delta_fila, delta_columna)
    # Horizontal, Vertical, Diagonal, Invertidas
    direcciones = [
        (0, 1), (1, 0), (1, 1), (1, -1), # Normales
        (0, -1), (-1, 0), (-1, -1), (-1, 1) # Invertidas (Mayor dificultad)
    ]

    # Ordenamos palabras de mayor a menor longitud (facilita el encaje)
    palabras.sort(key=len, reverse=True)

    for palabra in palabras:
        colocada = False
        intentos = 0
        
        # Intentamos colocar la palabra 100 veces en posiciones al azar
        while not colocada and intentos < 100:
            intentos += 1
            direccion = random.choice(direcciones)
            fila_inicio = random.randint(0, filas - 1)
            col_inicio = random.randint(0, columnas - 1)
            
            # Chequeamos si cabe
            fila, col = fila_inicio, col_inicio
            cabe = True
            
            for letra in palabra:
                # Verificar limites
                if not (0 <= fila < filas and 0 <= col < columnas):
                    cabe = False
                    break
                # Verificar colisión (casilla vacía o misma letra)
                if grid[fila][col] != ' ' and grid[fila][col] != letra:
                    cabe = False
                    break
                
                fila += direccion[0]
                col += direccion[1]
            
            # Si cabe, la escribimos
            if cabe:
                fila, col = fila_inicio, col_inicio
                coords = [] # Guardamos coordenadas para el frontend interactivo
                for letra in palabra:
                    grid[fila][col] = letra
                    coords.append((fila, col))
                    fila += direccion[0]
                    col += direccion[1]
                
                palabras_colocadas.append({
                    "palabra": palabra,
                    "coords": coords
                })
                colocada = True

    # 3. Rellenar espacios vacíos con letras aleatorias
    letras = string.ascii_uppercase
    grid_completo = [] # Copia para mostrar
    for f in range(filas):
        fila_letras = []
        for c in range(columnas):
            if grid[f][c] == ' ':
                fila_letras.append(random.choice(letras))
            else:
                fila_letras.append(grid[f][c])
        grid_completo.append(fila_letras)

    return grid_completo, palabras_colocadas

# =========================================================================
# === IX. GENERADOR DE DOCX PUPILETRAS (FICHA IMPRIMIBLE) ===
# =========================================================================

def generar_docx_pupiletras(grid, palabras_data, tema, grado):
    """
    Crea un archivo Word con la sopa de letras formateada para imprimir.
    """
    doc = Document()
    
    # 1. TÍTULO Y ENCABEZADO
    titulo = doc.add_heading(f"SOPA DE LETRAS: {tema.upper()}", 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(f"Nivel: {grado} | Generado por AulaMetrics").bold = True

    doc.add_paragraph("") # Espacio

    # 2. DIBUJAR LA GRILLA (TABLA)
    filas = len(grid)
    columnas = len(grid[0])
    
    # Creamos tabla
    table = doc.add_table(rows=filas, cols=columnas)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = False 
    
    # Configuración de celdas
    for i in range(filas):
        for j in range(columnas):
            cell = table.cell(i, j)
            cell.text = grid[i][j]
            
            # Formato de texto (Centrado y Grande)
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.runs[0]
            run.font.size = Pt(14)
            run.font.bold = True
            
            # Ajuste de ancho/alto (para que sea cuadrada)
            cell.width = Inches(0.4)
            cell.height = Inches(0.4)

    doc.add_paragraph("") # Espacio grande
    doc.add_paragraph("")

    # 3. LISTA DE PALABRAS A BUSCAR
    doc.add_heading("Palabras a encontrar:", level=2)
    
    # Usamos una tabla invisible para listar las palabras ordenadamente (3 columnas)
    lista_palabras = [item['palabra'] for item in palabras_data]
    lista_palabras.sort()
    
    num_cols_lista = 3
    num_rows_lista = (len(lista_palabras) + num_cols_lista - 1) // num_cols_lista
    
    list_table = doc.add_table(rows=num_rows_lista, cols=num_cols_lista)
    list_table.style = 'Table Grid' 
    
    idx = 0
    for r in range(num_rows_lista):
        for c in range(num_cols_lista):
            if idx < len(lista_palabras):
                cell = list_table.cell(r, c)
                cell.text = f"⬜ {lista_palabras[idx]}"
                idx += 1

    # 4. GUARDAR EN MEMORIA
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io


# =========================================================================
# === X. MOTOR JUEGO ROBOT (AHORCADO EDUCATIVO V2.0) ===
# =========================================================================

def generar_reto_ahorcado(tema, grado, cantidad):
    """
    Genera una lista de palabras y pistas para el juego del Robot.
    Retorna: list [{'palabra':Str, 'pista':Str}, ...]
    """
    if client is None:
        return []

    prompt = f"""
    Actúa como un diseñador de juegos educativos. 
    Necesito {cantidad} retos distintos para un juego tipo "Ahorcado" sobre el tema: "{tema}" para el grado: "{grado}".
    
    INSTRUCCIONES:
    1. Elige palabras clave (conceptos importantes) relacionadas con el tema.
    2. Las palabras deben ser en MAYÚSCULAS, SIN TILDES y SIN ESPACIOS (Ej: "ECOSISTEMA", no "Ecosistema" ni "Árbol").
    3. Escribe una pista pedagógica clara para cada palabra, adecuada al nivel del estudiante.
    
    FORMATO JSON OBLIGATORIO (Array de objetos):
    [
        {{
            "palabra": "PALABRAUNO",
            "pista": "Texto de la pista uno..."
        }},
        {{
            "palabra": "PALABRADOS",
            "pista": "Texto de la pista dos..."
        }}
    ]
    """

    try:
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generando ahorcado: {e}")
        return []





