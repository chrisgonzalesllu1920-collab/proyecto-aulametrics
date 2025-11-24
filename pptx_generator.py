import io
import json
from pptx import Presentation
from pptx.util import Pt

def crear_ppt_desde_data(json_texto):
    """
    Recibe el texto JSON generado por Gemini, lo limpia y crea 
    una presentación de 5 diapositivas automáticamente.
    """
    # 1. Crear presentación vacía
    prs = Presentation()
    
    # 2. Intentar leer los datos JSON
    try:
        # A veces la IA pone ```json al principio, lo limpiamos
        json_limpio = json_texto.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_limpio)
    except Exception as e:
        # Si falla el JSON, devolvemos error (o una ppt de error)
        print(f"Error parseando JSON: {e}")
        return None

    # --- DIAPOSITIVA 1: PORTADA (Layout 0) ---
    if 'slide_1' in data:
        info = data['slide_1']
        slide = prs.slides.add_slide(prs.slide_layouts[0]) # 0 = Title Slide
        slide.shapes.title.text = info.get('titulo', 'Sin Título')
        # El placeholder[1] suele ser el subtítulo
        if len(slide.placeholders) > 1:
            slide.placeholders[1].text = info.get('subtitulo', '')

    # --- DIAPOSITIVAS 2 a 5: CONTENIDO (Layout 1) ---
    # Layout 1 = Título + Contenido (Viñetas)
    keys_contenido = ['slide_2', 'slide_3', 'slide_4', 'slide_5']
    
    for key in keys_contenido:
        if key in data:
            info = data[key]
            slide = prs.slides.add_slide(prs.slide_layouts[1]) 
            
            # Título de la diapositiva
            slide.shapes.title.text = info.get('titulo', '')
            
            # Cuerpo (Texto o Puntos)
            # Detectamos si viene como "contenido" (texto) o "puntos" (lista)
            contenido_raw = info.get('contenido') or info.get('puntos') or ""
            
            # Usamos el cuadro de texto principal
            tf = slide.placeholders[1].text_frame
            tf.clear() # Limpiamos por si acaso

            if isinstance(contenido_raw, list):
                # Si es una lista, agregamos viñetas
                for punto in contenido_raw:
                    p = tf.add_paragraph()
                    p.text = str(punto)
                    p.level = 0 # Nivel de indentación principal
            else:
                # Si es texto simple
                p = tf.add_paragraph()
                p.text = str(contenido_raw)

    # 3. Guardar en memoria
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    
    return buffer
