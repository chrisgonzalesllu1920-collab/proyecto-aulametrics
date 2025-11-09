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
# (Esta sección no ha cambiado)
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
            model='gemini-1.5-flash', 
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
# (Esta sección no ha cambiado)
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
# (Esta sección no ha cambiado)
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
# === IV. FUNCIÓN DE GENERACIÓN DE SESIÓN (MODO DE DIAGNÓSTICO) ===
# =========================================================================

def generar_sesion_aprendizaje(nivel, grado, ciclo, area, competencias_lista, capacidades_lista, estandar_texto, tematica, tiempo):
    """
    MODO DE DIAGNÓSTICO: Esta función listará los modelos de IA disponibles
    en lugar de generar una sesión.
    """
    
    if client is None:
        return "⚠️ **Error de Configuración de IA:** El cliente de Gemini no se pudo inicializar. Revisa tus secretos (secrets.toml)."

    try:
        # --- ¡AQUÍ ESTÁ EL CÓDIGO DE DIAGNÓSTICO! ---
        st.info("Iniciando modo de diagnóstico de IA...")
        
        lista_de_modelos = []
        for m in client.models.list():
            # Filtramos solo los modelos que PUEDEN generar contenido
            if 'generateContent' in m.supported_generation_methods:
                lista_de_modelos.append(m.name)
        
        # Formateamos la lista para mostrarla
        modelos_texto = "\n".join(f"- `{model}`" for model in lista_de_modelos)
        
        return f"""
        **Diagnóstico Completado: Modelos Disponibles**
        
        Estos son los nombres de modelos exactos que tu API Key gratuita puede usar:
        
        {modelos_texto}
        
        (Por favor, copia esta lista y pégala en nuestro chat para que pueda elegir el motor correcto)
        """

    except Exception as e:
        return f"Error al intentar listar los modelos: {e}"


