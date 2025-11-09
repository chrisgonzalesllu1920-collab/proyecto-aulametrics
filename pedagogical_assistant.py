import streamlit as st
import os
import pandas as pd
import io
import re 
from google import genai
from google.genai.errors import APIError
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor

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
    Genera propuestas de mejora usando el modelo de IA de Google (Gemini) y retorna el texto.
    """
    
    if client is None:
        return "⚠️ **Error de Configuración de IA:** El cliente de Gemini no se pudo inicializar. Revisa tus secretos (secrets.toml)."
        
    grado = critical_comp_info['grado']
    nivel = critical_comp_info['nivel']
    area = critical_comp_info['area']
    competencia = critical_comp_info['nombre']
    
    prompt = f"""
    Eres un asistente pedagógico experto en currículo escolar para {nivel} - {grado}.
    Tu tarea es generar **5 propuestas** de intervención didáctica **innovadoras, concretas y específicas**
    para abordar la dificultad identificada en la siguiente competencia:

    **Área:** {area}
    **Grado:** {grado}
    **Competencia a mejorar:** "{competencia}"
    **Análisis de dificultad:** {critical_comp_info['analisis']}

    Las **5 propuestas** deben estar directamente orientadas al desarrollo de los **saberes clave de esa competencia específica**.
    Evita sugerencias genéricas.

    **REGLAS DE FORMATO ESTRICTAS:**
    1.  Usa **exclusivamente Markdown simple**.
    2.  Formatea la respuesta con un encabezado principal y una lista numerada del 1 al 5.
    3.  **NO** incluyas **ningún** código HTML, CSS, o etiquetas <div>, <span> o <style>.
    4.  El fondo debe ser transparente (sin color).
    5.  El texto debe ser del color estándar (negro).
    6.  No añadas introducciones o conclusiones adicionales.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
        )
        return response.text
    except APIError as e:
        return f"❌ **Error al contactar la IA:** Se produjo un error en la API de Google (Código: {e}). Revisa tu clave y la cuota de uso."
    except Exception as e:
        return f"❌ **Error desconocido:** {e}"


# =========================================================================
# === II. FUNCIÓN DE EXPORTACIÓN A WORD (DOCX) ===
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
            document.add_heading(re.sub(r'^#\s*', '', line).strip(), level=1)
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
# === (PROMPT AFINADO - Corrección de Formato ESTRICTO) ===
# =========================================================================

def generar_sesion_aprendizaje(nivel, grado, ciclo, area, competencias_lista, capacidades_lista, estandar_texto, tematica, tiempo):
    """
    Genera una sesión de aprendizaje completa usando la IA, basada en la plantilla del usuario.
    """
    
    if client is None:
        return "⚠️ **Error de Configuración de IA:** El cliente de Gemini no se pudo inicializar. Revisa tus secretos (secrets.toml)."

    # 1. Convertir listas a texto formateado para el prompt
    competencias_str = "\n".join(f"- {comp}" for comp in competencias_lista)
    capacidades_str = "\n".join(f"- {cap}" for cap in capacidades_lista)

    # 2. Construir el Mega-Prompt
    prompt = f"""
    Actúa como un docente experto y diseñador curricular en el sistema educativo peruano.
    Tu tarea es generar una sesión de aprendizaje completa basada en los siguientes datos y plantillas.
    Debes seguir el formato Markdown exacto solicitado.

    ## DATOS DE ENTRADA:
    - **Nivel:** {nivel}
    - **Grado:** {grado}
    - **Ciclo:** {ciclo}
    - **Área:** {area}
    - **Tema (Temática):** {tematica}
    - **Duración:** {tiempo}

    ## RECURSOS PEDAGÓGICOS (Contexto):
    
    **Competencia(s) Seleccionada(s):**
    {competencias_str}

    **Capacidad(es) Correspondiente(s):**
    {capacidades_str}

    **Estándar(es) del Ciclo (Descripción del Nivel de Desarrollo):**
    "{estandar_texto}"

    ## REGLA DE ORO (CRITERIOS DE EVALUACIÓN):
    ¡Atención! El estándar de competencia que te he dado (en "Descripción del Nivel de Desarrollo") es la meta para el **final** del Ciclo {ciclo}.
    El docente ha seleccionado el **{grado}**. 
    Tu tarea es generar **Criterios de Evaluación** que estén *adaptados* a ese {grado} específico. Los criterios deben ser un paso intermedio y progresivo para alcanzar el estándar final, y deben estar directamente relacionados con el **Tema ({tematica})** y las **Capacidades**.

    ## PLANTILLA DE SALIDA (Formato Requerido):
    Genera la sesión usando este formato Markdown. Completa cada sección según las plantillas e instrucciones.

    ### SESIÓN DE APRENDIZAJE – N° 

    **I. DATOS GENERALES:**
    * **Título:** [Genera un título creativo para la sesión, basado en la Temática: {tematica}]
    * **Unidad de Aprendizaje:** * **Duración:** {tiempo}
    * **Fecha:** * **Ciclo:** {ciclo}
    * **Grado:** {grado}
    * **Sección:** * **Docente:** **II. PROPÓSITO DE LA SESIÓN:**
    * [Genera el propósito siguiendo esta estructura: (Verbo en infinitivo) + ¿qué? (el tema) + ¿cómo? (estrategia metodológica) + ¿para qué? (el fin de la sesión)]

    **III. COMPETENCIAS Y CAPACIDADES:**
    
    | COMPETENCIA | CAPACIDAD | CRITERIOS DE EVALUACIÓN |
    | :--- | :--- | :--- |
    [Aquí debes rellenar la tabla, fila por fila, usando los datos de entrada. NO incluyas la columna 'DESEMPEÑO'.]

    **REGLAS ESTRICTAS PARA LA TABLA (image_71ebfc.png):**
    - Rellena la tabla, fila por fila, con las competencias, capacidades y criterios.
    - **¡PROHIBIDO usar la etiqueta `<br>`!**
    - Para saltos de línea dentro de una celda, **DEBES** usar una lista de viñetas con **guiones (`-`)**.
    - Los Criterios de Evaluación deben alinearse estrictamente con el Estándar y el Grado.

    **DATOS PARA LA TABLA:**
    - **Competencia(s):** {competencias_str}
    - **Capacidad(es):** {capacidades_str}
    - **Criterios de Evaluación:** [Genera aquí 3-4 Criterios de Evaluación por competencia, usando guiones (`-`).]

    **IV. ENFOQUE TRANSVERSAL:**
    (Deja esta sección vacía)
    
    **V. SECUENCIA DIDÁCTICA (Momentos de la Sesión):**

    **INICIO** (Tiempo estimado: [Especificar un tiempo corto, ej: 15 minutos])
    * **Motivación:** [Genera una actividad corta de motivación]
    * **Saberes previos:** [Genera 2-3 preguntas para explorar saberes previos sobre {tematica}]
    * **Conflicto cognitivo:** [Genera 1 pregunta de conflicto cognitivo]
    * **Presentación del propósito:** [Indica que el docente presenta el propósito (definido en la sección II) y los criterios de evaluación.]

    **DESARROLLO** (Tiempo estimado: [Especificar, debe ser la mayor parte de la Duración total])
    * **Gestión y acompañamiento:** [Describe aquí los procesos didácticos, métodos y estrategias que el docente usará para desarrollar las competencias seleccionadas, abordando el tema: {tematica}]

    **CIERRE** (Tiempo estimado: [Especificar un tiempo corto, ej: 15 minutos])
    * **Evaluación o transferencia de lo aprendido:** [Genera aquí una actividad corta de evaluación formativa o transferencia (por ejemplo, un reto breve, una pregunta de aplicación práctica).]
    * **Metacognición:** [Genera aquí 2-3 preguntas de metacognición (ej: ¿Qué aprendimos hoy? ¿Cómo lo aprendimos? ¿Para qué nos sirve?)]
    
    **VI. MATERIALES O RECURSOS:**
    * [Presenta una lista (bullet points) de materiales o recursos necesarios para esta sesión]

    **VII. FIRMAS:**

    \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
    DIRECTOR

    \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
    DOCENTE DE ({area})
    """
    
    try:
        # Usamos el modelo 'flash' que sabemos que funciona
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error al contactar la IA: {e}"
