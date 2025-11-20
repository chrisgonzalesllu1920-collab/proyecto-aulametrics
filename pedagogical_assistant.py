import streamlit as st
import os
import pandas as pd
import io
import re 
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
            model='models/gemini-2.5-pro', 
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
# === II-B. EXPORTACIÓN A WORD INTELIGENTE (Sesión) ===
# =========================================================================
def generar_docx_sesion(sesion_markdown_text, area_docente):
    """
    Convierte el texto Markdown de la sesión generada por la IA en un 
    documento de Word (.docx) y lo devuelve en bytes.
    Reconstruye la tabla de competencias y formatea correctamente.
    """
    document = Document()
    
    def process_markdown_to_runs(paragraph, text):
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                paragraph.add_run(part[2:-2]).bold = True
            else:
                paragraph.add_run(part)

    def add_list_item(paragraph, text, style='List Bullet'):
        cleaned_line = re.sub(r'^\*\s*|^\-\s*', '', text).strip()
        paragraph.style = style
        process_markdown_to_runs(paragraph, cleaned_line)

    lines = sesion_markdown_text.split('\n')
    
    # Variables de estado para la tabla
    in_competencies_section = False
    current_competencia_text = ""
    current_capacidades_list = []
    current_criterios_list = []
    table = None
    current_state = 0 

    def flush_competencia_to_table(table, comp_text, cap_list, crit_list):
        if not comp_text: return 
            
        row_cells = table.add_row().cells
        process_markdown_to_runs(row_cells[0].paragraphs[0], comp_text)
        
        if cap_list:
            row_cells[1].paragraphs[0].text = "" 
            if len(row_cells[1].paragraphs) > 0:
                p = row_cells[1].paragraphs[0]
                if not p.text: p._element.getparent().remove(p._element)
            for item in cap_list:
                p = row_cells[1].add_paragraph()
                add_list_item(p, item)
        
        if crit_list:
            row_cells[2].paragraphs[0].text = ""
            if len(row_cells[2].paragraphs) > 0:
                p = row_cells[2].paragraphs[0]
                if not p.text: p._element.getparent().remove(p._element)
            for item in crit_list:
                p = row_cells[2].add_paragraph()
                add_list_item(p, item)

    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith('###'):
            if in_competencies_section and current_competencia_text and table is not None:
                flush_competencia_to_table(table, current_competencia_text, current_capacidades_list, current_criterios_list)
                current_competencia_text = "" 
            
            document.add_heading(re.sub(r'^###\s*', '', line).strip(), level=3) 
            if "SESIÓN DE APRENDIZAJE" in line:
                document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                document.paragraphs[-1].style = 'Title' 
            in_competencies_section = False
            
        elif line.startswith('##'):
            document.add_heading(re.sub(r'^##\s*', '', line).strip(), level=1)
            in_competencies_section = False
            
        elif line.startswith('#'):
            document.add_heading(re.sub(r'^#\s*', '', line).strip(), level=0)
            in_competencies_section = False
        
        elif line.startswith('**I.') or line.startswith('**II.') or \
             line.startswith('**IV.') or line.startswith('**V.') or \
             line.startswith('**VI.') or line.startswith('**VII.'):
            if in_competencies_section and current_competencia_text and table is not None:
                flush_competencia_to_table(table, current_competencia_text, current_capacidades_list, current_criterios_list)
                current_competencia_text = "" 
                
            document.add_heading(line.replace('**', ''), level=2)
            in_competencies_section = False
        
        # Lógica Tabla Competencias
        elif line.startswith('**III. COMPETENCIAS'):
            document.add_heading(line.replace('**', ''), level=2)
            in_competencies_section = True
            current_state = 0 
            table = document.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'COMPETENCIA'
            hdr_cells[1].text = 'CAPACIDAD'
            hdr_cells[2].text = 'CRITERIOS DE EVALUACIÓN'
            for cell in hdr_cells:
                cell.paragraphs[0].runs[0].bold = True
                
        elif in_competencies_section:
            if line.startswith('---'):
                if table is not None:
                    flush_competencia_to_table(table, current_competencia_text, current_capacidades_list, current_criterios_list)
                current_competencia_text = ""
                current_capacidades_list = []
                current_criterios_list = []
                current_state = 0
            elif line.startswith('**Competencia:') or line.startswith('Competencia:'):
                current_competencia_text = re.sub(r'^\*\*Competencia:\*\*|Competencia:', '', line).strip()
                current_capacidades_list = []
                current_criterios_list = []
                current_state = 0 
            elif line.startswith('**Capacidades:') or line.startswith('Capacidades:'):
                current_state = 1 
            elif line.startswith('**Criterios de Evaluación:') or line.startswith('Criterios de Evaluación:'):
                current_state = 2 
            elif line.startswith('-') or line.startswith('*'):
                if current_state == 1: current_capacidades_list.append(line)
                elif current_state == 2: current_criterios_list.append(line)
        
        elif line.startswith('*') or line.startswith('-'):
            paragraph = document.add_paragraph(style='List Bullet')
            add_list_item(paragraph, line)
            
        elif re.match(r'^\d+\.', line):
            paragraph = document.add_paragraph(style='List Number')
            cleaned_line = re.sub(r'^\d+\.\s*', '', line).strip()
            process_markdown_to_runs(paragraph, cleaned_line)
            
        elif line.startswith('___'):
            p = document.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
        else:
            if line: 
                paragraph = document.add_paragraph()
                process_markdown_to_runs(paragraph, line)
    
    if in_competencies_section and current_competencia_text and table is not None:
        flush_competencia_to_table(table, current_competencia_text, current_capacidades_list, current_criterios_list)
    
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
# === (Versión ACTUALIZADA CON METODOLOGÍA DINÁMICA Y PENSAMIENTO CRÍTICO) ===
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
        # 1. Intentar con modelo Pro
        response = client.models.generate_content(
            model='models/gemini-2.5-pro',
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
