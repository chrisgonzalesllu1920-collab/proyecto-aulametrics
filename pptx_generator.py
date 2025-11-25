import io
import json
import requests
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# --- CONFIGURACIÓN DE COLORES ---
COLOR_PRIMARIO = RGBColor(0, 51, 102)  # Azul Oscuro (Institucional)
COLOR_TEXTO_BLANCO = RGBColor(255, 255, 255)

def obtener_imagen_ia(descripcion_en_ingles):
    """
    Descarga imagen de Pollinations. Si falla, devuelve None.
    """
    if not descripcion_en_ingles:
        return None
    try:
        # Usamos el modelo 'flux' que es rápido y bueno
        prompt = descripcion_en_ingles.replace(" ", "%20")
        # Pedimos una imagen apaisada (4:3) para que encaje bien
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=768&nologo=true&model=flux"
        
        # Timeout de 10 segundos para darle tiempo a generar
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return io.BytesIO(response.content)
    except Exception as e:
        print(f"Error descargando imagen: {e}")
        return None
    return None

def agregar_barra_superior(slide, titulo_texto):
    """
    Dibuja un rectángulo azul arriba y pone el título dentro en blanco.
    """
    # 1. Dibujar Barra Azul en el tope
    left = top = Inches(0)
    width = Inches(10) # Ancho total de la diapositiva
    height = Inches(1.3) # Alto de la barra
    
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_PRIMARIO
    shape.line.fill.background() # Sin borde negro
    
    # 2. Poner el Título encima (borrando el original para no duplicar)
    if slide.shapes.title:
        # Intentamos quitar el placeholder original si estorba
        try:
            sp = slide.shapes.title
            sp.element.getparent().remove(sp.element)
        except:
            pass
        
    # Creamos un cuadro de texto nuevo sobre la barra azul
    textbox = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(9), Inches(1))
    tf = textbox.text_frame
    p = tf.paragraphs[0]
    p.text = titulo_texto
    p.font.color.rgb = COLOR_TEXTO_BLANCO
    p.font.size = Pt(32)
    p.font.bold = True

def crear_ppt_desde_data(json_texto):
    prs = Presentation()
    
    try:
        json_limpio = json_texto.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_limpio)
    except Exception:
        return None

    # --- SLIDE 1: PORTADA ---
    if 'slide_1' in data:
        info = data['slide_1']
        slide = prs.slides.add_slide(prs.slide_layouts[6]) # 6 = Blank (Lienzo limpio)
        
        # Fondo Azul Completo
        background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(7.5))
        background.fill.solid()
        background.fill.fore_color.rgb = COLOR_PRIMARIO
        
        # Título Centrado
        tb_title = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(2))
        p = tb_title.text_frame.paragraphs[0]
        p.text = info.get('titulo', 'Sin Título')
        p.font.color.rgb = COLOR_TEXTO_BLANCO
        p.font.size = Pt(44)
        p.font.bold = True
        p.alignment = 2 # Center

        # Subtítulo
        tb_sub = slide.shapes.add_textbox(Inches(1), Inches(4.5), Inches(8), Inches(1))
        p_sub = tb_sub.text_frame.paragraphs[0]
        p_sub.text = info.get('subtitulo', '')
        p_sub.font.color.rgb = RGBColor(220, 220, 220) # Gris claro
        p_sub.font.size = Pt(24)
        p_sub.alignment = 2

    # --- SLIDES 2-7: CONTENIDO ---
    keys = ['slide_2', 'slide_3', 'slide_4', 'slide_5', 'slide_6', 'slide_7']
    
    for key in keys:
        if key in data:
            info = data[key]
            slide = prs.slides.add_slide(prs.slide_layouts[6]) # Blank
            
            # 1. Diseño: Barra Superior Azul
            agregar_barra_superior(slide, info.get('titulo', ''))
            
            # 2. Texto (Mitad Izquierda)
            # Inches(0.5) margen izq, Inches(1.5) bajamos después de la barra
            tb_body = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4.5), Inches(5.5))
            tf = tb_body.text_frame
            tf.word_wrap = True
            
            contenido = info.get('contenido') or info.get('puntos') or ""
            
            def add_p(text, bullet=False):
                p = tf.add_paragraph()
                p.text = str(text)
                p.font.size = Pt(18)
                p.space_after = Pt(10) # Espacio entre párrafos
                if bullet: 
                    p.text = "• " + str(text)

            if isinstance(contenido, list):
                for x in contenido: add_p(x, True)
            else:
                add_p(contenido)

            # 3. Imagen (Mitad Derecha)
            desc = info.get('descripcion_imagen', '')
            if desc:
                img_bytes = obtener_imagen_ia(desc)
                if img_bytes:
                    try:
                        # Colocamos la imagen a la derecha (Inches 5.2)
                        slide.shapes.add_picture(img_bytes, Inches(5.2), Inches(1.5), width=Inches(4.3))
                    except:
                        pass # Si falla insertar, queda el hueco

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer
