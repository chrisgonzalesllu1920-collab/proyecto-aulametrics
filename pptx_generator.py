import io
import json
from pptx import Presentation
from pptx.util import Pt

def crear_ppt_desde_data(json_texto):
    """
    Crea una presentación de 7 diapositivas.
    """
    prs = Presentation()
    
    try:
        json_limpio = json_texto.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_limpio)
    except Exception as e:
        print(f"Error parseando JSON: {e}")
        return None

    # --- DIAPOSITIVA 1: PORTADA ---
    if 'slide_1' in data:
        info = data['slide_1']
        slide = prs.slides.add_slide(prs.slide_layouts[0]) 
        
        # Título
        title = slide.shapes.title
        title.text = info.get('titulo', 'Sin Título')
        title.text_frame.paragraphs[0].font.size = Pt(40)
        
        # Subtítulo
        if len(slide.placeholders) > 1:
            subtitle = slide.placeholders[1]
            subtitle.text = info.get('subtitulo', '')
            subtitle.text_frame.paragraphs[0].font.size = Pt(24)

    # --- DIAPOSITIVAS 2 a 7: CONTENIDO ---
    # Actualizamos la lista para incluir slide_7
    keys_contenido = ['slide_2', 'slide_3', 'slide_4', 'slide_5', 'slide_6', 'slide_7']
    
    for key in keys_contenido:
        if key in data:
            info = data[key]
            slide = prs.slides.add_slide(prs.slide_layouts[1]) 
            
            # Título
            title = slide.shapes.title
            title.text = info.get('titulo', '')
            title.text_frame.paragraphs[0].font.size = Pt(32)
            
            # Cuerpo
            contenido_raw = info.get('contenido') or info.get('puntos') or ""
            
            tf = slide.placeholders[1].text_frame
            tf.clear() 

            def add_text(frame, text, bullet=False):
                p = frame.add_paragraph()
                p.text = str(text)
                p.font.size = Pt(20) # Tamaño seguro
                if not bullet:
                    p.level = 0

            if isinstance(contenido_raw, list):
                for punto in contenido_raw:
                    add_text(tf, punto, bullet=True)
            else:
                add_text(tf, contenido_raw, bullet=False)

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    
    return buffer
