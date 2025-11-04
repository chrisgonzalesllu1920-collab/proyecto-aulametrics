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
# === FUNCIÓN DE GENERACIÓN DE IA (Prompt Corregido) ===
# =========================================================================

def generate_ai_suggestions(critical_comp_info):
    """
    Genera propuestas de mejora usando el modelo de IA de Google (Gemini) y retorna el texto.
    """
    
    try:
        gemini_key = st.secrets['gemini']['api_key']
        client = genai.Client(api_key=gemini_key) 
    except KeyError:
        return "⚠️ **Error de Configuración de IA:** No se encontró la clave de Gemini. Asegúrate de que tienes el archivo `.streamlit/secrets.toml` configurado."
    except Exception as e:
        return f"❌ **Error al inicializar el cliente de Gemini:** {e}"
        
    
    grado = critical_comp_info['grado']
    nivel = critical_comp_info['nivel']
    area = critical_comp_info['area']
    competencia = critical_comp_info['nombre']
    
    # === INICIO DE LA CORRECCIÓN DEL PROMPT ===
    # Añadimos instrucciones explícitas para NO usar HTML/CSS.
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
    # === FIN DE LA CORRECCIÓN DEL PROMPT ===
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Asegúrate de tener acceso a este modelo
            contents=prompt,
        )
        return response.text
    except APIError as e:
        return f"❌ **Error al contactar la IA:** Se produjo un error en la API de Google (Código: {e}). Revisa tu clave y la cuota de uso."
    except Exception as e:
        return f"❌ **Error desconocido:** {e}"


# =========================================================================
# === FUNCIÓN DE EXPORTACIÓN A WORD (DOCX) ===
# =========================================================================

def generate_docx_report(analisis_results, sheet_name, selected_comp_limpio, ai_report_text):
    """
    Genera un archivo DOCX a partir del informe de la IA, limpiando los símbolos de Markdown y aplicando formato.
    """
    document = Document()
    
    # Obtener información general
    result = analisis_results[sheet_name]
    general_data = result.get('generalidades', {})
    grado = general_data.get('grado', 'Desconocido')
    nivel = general_data.get('nivel', 'Desconocido')
    
    # 1. Título del Documento
    document.add_heading(f'INFORME DE PROPUESTAS PEDAGÓGICAS', 0)
    
    # 2. Diagnóstico
    document.add_heading('Datos de Contexto y Diagnóstico', level=1)
    
    # Añadir Contexto
    document.add_paragraph(f"Nivel/Grado: {nivel} / {grado}")
    document.add_paragraph(f"Área Analizada: {sheet_name}")
    
    p_comp = document.add_paragraph()
    p_comp.add_run(f"Competencia a Abordar: ").bold = True
    p_comp.add_run(selected_comp_limpio)
    
    document.add_heading('Propuestas de Intervención (Generadas por IA)', level=1)
    
    # 3. Contenido de las Propuestas (procesar el texto Markdown de la IA)
    
    # Función auxiliar para limpiar y formatear texto Markdown
    def process_markdown_to_runs(paragraph, text):
        # Este regex busca texto envuelto en ** (negrita) o * (cursiva)
        # y también maneja los que deberían ser literales
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
            
        # Saltar encabezados genéricos o repetidos
        if "propuestas de intervención didáctica" in line.lower() or "propuestas de intervención (generadas por ia)" in line.lower():
            continue

        # Lógica para manejar títulos
        if line.startswith('###'):
            document.add_heading(re.sub(r'^###\s*', '', line).strip(), level=2)
        elif line.startswith('##'):
            document.add_heading(re.sub(r'^##\s*', '', line).strip(), level=1)
        elif line.startswith('#'):
            document.add_heading(re.sub(r'^#\s*', '', line).strip(), level=1)
            
        # Listas Numeradas (Propuestas principales: 1., 2., 3., etc.)
        elif re.match(r'^\d+\.', line):
            paragraph = document.add_paragraph(style='List Number')
            # Eliminar el número de lista del inicio de la línea para que Word lo añada
            cleaned_line = re.sub(r'^\d+\.\s*', '', line).strip()
            process_markdown_to_runs(paragraph, cleaned_line)
            
        # Listas con asteriscos (Subpuntos dentro de las propuestas: *Saberes clave, *Descripción)
        elif line.startswith('*'):
            paragraph = document.add_paragraph(style='List Bullet')
            # Eliminar solo el primer asterisco y espacio
            cleaned_line = re.sub(r'^\*\s*', '', line).strip()
            process_markdown_to_runs(paragraph, cleaned_line)
            
        # Párrafos de texto normal
        else:
            if line: # Asegurarse de que no sea una línea vacía
                paragraph = document.add_paragraph()
                process_markdown_to_runs(paragraph, line)
                
    # Guardar el documento en un buffer en memoria
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


# =========================================================================
# === FUNCIÓN PRINCIPAL LLAMADA DESDE APP.PY (Corregida) ===
# =========================================================================

def generate_suggestions(analisis_results, selected_sheet_name, selected_comp_limpio):
    """
    Calcula la dificultad de la competencia seleccionada por el usuario, genera el informe y lo muestra.
    Retorna el texto del informe de la IA.
    """
    
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
        
        # === INICIO DE LA CORRECCIÓN ===
        # Esta función ya no imprime el resultado (ni st.markdown ni st.error).
        # Solo retorna el texto. app.py se encargará de mostrarlo.
        return ai_response_text 
        # === FIN DE LA CORRECCIÓN ===