import io
import json
import requests  # <--- Nueva librería para descargar de internet
from pptx import Presentation
from pptx.util import Pt, Inches

def obtener_imagen_ia(descripcion_en_ingles):
    """
    Usa la API gratuita de Pollinations.ai para generar una imagen
    basada en la descripción de texto.
    """
    if not descripcion_en_ingles:
        return None
        
    try:
        # Limpiamos el prompt y creamos la URL mágica
        prompt_limpio = descripcion_en_ingles.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{prompt_limpio}?width=800&height=600&nologo=true&model=flux"
        
        # Descargamos la imagen
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return io.BytesIO(response.content)
    except Exception as e:
        print(f"No se pudo descargar la imagen: {e}")
        return None
    return None

def crear_ppt_desde_data(json_texto):
    """
    Crea una presentación de 7 diapositivas con IMÁGENES GENERADAS POR IA.
    Diseño: Texto a la Izquierda / Imagen a la Derecha.
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
        
        # Textos
        title = slide.shapes.title
        title.text = info.get('titulo', 'Sin Título')
        
        if len(slide.placeholders) > 1:
            subtitle = slide.placeholders[1]
            subtitle.text = info.get('subtitulo', '')

        # Intentamos poner una imagen de fondo o lateral pequeña si hay descripción
        # (Para la portada, por ahora la dejamos limpia o añadiremos logo después)

    # --- DIAPOSITIVAS 2 a 7: CONTENIDO CON IMÁGENES ---
    keys_contenido = ['slide_2', 'slide_3', 'slide_4', 'slide_5', 'slide_6', 'slide_7']
    
    for key in keys_contenido:
        if key in data:
            info = data[key]
            # Usamos Layout 1 (Título y Objeto) pero lo modificaremos manualmente
            slide = prs.slides.add_slide(prs.slide_layouts[1]) 
            
            # 1. TÍTULO
            title = slide.shapes.title
            title.text = info.get('titulo', '')
            title.text_frame.paragraphs[0].font.size = Pt(32)
            
            # 2. MANEJO DEL TEXTO (IZQUIERDA)
            # Obtenemos el cuadro de texto principal
            body_shape = slide.placeholders[1]
            
            # Lo redimensionamos para que ocupe solo la mitad izquierda
            # (Ancho total slide es 10 pulgadas. Dejamos 5 para texto)
            body_shape.left = Inches(0.5)
            body_shape.width = Inches(4.5)
            
            tf = body_shape.text_frame
            tf.clear() 

            contenido_raw = info.get('contenido') or info.get('puntos') or ""
            
            def add_text(frame, text, bullet=False):
                p = frame.add_paragraph()
                p.text = str(text)
                p.font.size = Pt(18) # Letra un poco más chica para que quepa
                if not bullet:
                    p.level = 0
                # Ajustamos espaciado
                p.space_after = Pt(6)

            if isinstance(contenido_raw, list):
                for punto in contenido_raw:
                    add_text(tf, punto, bullet=True)
            else:
                add_text(tf, contenido_raw, bullet=False)
            
            # 3. MANEJO DE LA IMAGEN (DERECHA)
            descripcion = info.get('descripcion_imagen', '')
            if descripcion:
                imagen_bytes = obtener_imagen_ia(descripcion)
                if imagen_bytes:
                    # Insertamos la imagen a la derecha
                    # Left: 5.5 pulgadas, Top: 2 pulgadas
                    slide.shapes.add_picture(imagen_bytes, Inches(5.2), Inches(2), width=Inches(4.3))

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    
    return buffer
