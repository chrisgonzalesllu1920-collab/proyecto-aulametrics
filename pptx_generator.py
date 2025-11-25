import io
import json
import requests
from urllib.parse import quote
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.enum.dml import MSO_THEME_COLOR

# --- 1. CONFIGURACIÓN DE COLORES INTELIGENTES ---
COLORES_TEMATICOS = {
    "Matemática": RGBColor(25, 55, 109),       
    "Ciencia": RGBColor(40, 80, 40),           
    "Tecnología": RGBColor(70, 70, 70),        
    "Comunicación": RGBColor(160, 20, 20),     
    "Sociales": RGBColor(180, 90, 20),         
    "Arte": RGBColor(140, 20, 140),            
    "Default": RGBColor(0, 51, 102)            
}

def detectar_color(json_data):
    try:
        subtitulo = json_data.get('slide_1', {}).get('subtitulo', '').lower()
        if "matem" in subtitulo: return COLORES_TEMATICOS["Matemática"]
        if "cien" in subtitulo or "ambien" in subtitulo: return COLORES_TEMATICOS["Ciencia"]
        if "comuni" in subtitulo or "letras" in subtitulo: return COLORES_TEMATICOS["Comunicación"]
        if "social" in subtitulo or "civica" in subtitulo: return COLORES_TEMATICOS["Sociales"]
        if "arte" in subtitulo: return COLORES_TEMATICOS["Arte"]
    except:
        pass
    return COLORES_TEMATICOS["Default"]

# --- 2. DESCARGA DE IMÁGENES ROBUSTA ---
def obtener_imagen_ia(descripcion_en_ingles):
    if not descripcion_en_ingles: return None
    
    try:
        prompt_seguro = quote(descripcion_en_ingles)
        url = f"https://image.pollinations.ai/prompt/{prompt_seguro}?width=1024&height=768&nologo=true&model=flux"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        # Aumentamos el timeout a 20 segundos
        response = requests.get(url, headers=headers, timeout=20) 
        if response.status_code == 200:
            return io.BytesIO(response.content)
    except Exception as e:
        print(f"Error imagen: {e}")
        return None
    return None

# --- 3. DIBUJADO DE BARRA ---
def agregar_barra_superior(slide, titulo_texto, color_tema):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(1.3))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color_tema
    shape.line.fill.background()
    
    if slide.shapes.title:
        try: slide.shapes.title.element.getparent().remove(slide.shapes.title.element)
        except: pass
        
    textbox = slide.shapes.add_textbox(Inches(0.2), Inches(0.1), Inches(9.6), Inches(1.1))
    tf = textbox.text_frame
    tf.vertical_anchor = MSO_SHAPE.RECTANGLE 
    p = tf.paragraphs[0]
    p.text = titulo_texto
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.font.size = Pt(30)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER # Aseguramos centrado horizontal

def crear_ppt_desde_data(json_texto):
    prs = Presentation()
    
    try:
        json_limpio = json_texto.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_limpio)
    except Exception:
        return None

    color_actual = detectar_color(data)

    # --- SLIDE 1: PORTADA ---
    if 'slide_1' in data:
        info = data['slide_1']
        slide = prs.slides.add_slide(prs.slide_layouts[6]) 
        
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color_actual
        
        # CORRECCIÓN DE ENCUADRE DE TÍTULO Y SUBTÍTULO
        # Título - Más ancho y centrado
        tb_title = slide.shapes.add_textbox(Inches(0.5), Inches(2.2), Inches(9), Inches(2.5))
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True # Permite que el texto se ajuste
        p = tf_title.paragraphs[0]
        p.text = info.get('titulo', 'Sin Título')
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.size = Pt(40) 
        p.font.bold = True
        p.alignment = PP_ALIGN.CENTER 

        # Subtítulo - Más ancho y centrado
        tb_sub = slide.shapes.add_textbox(Inches(0.5), Inches(4.7), Inches(9), Inches(1))
        tf_sub = tb_sub.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = info.get('subtitulo', '')
        p_sub.font.color.rgb = RGBColor(230, 230, 230)
        p_sub.font.size = Pt(22)
        p_sub.alignment = PP_ALIGN.CENTER

    # --- SLIDES 2-7: CONTENIDO ---
    keys = ['slide_2', 'slide_3', 'slide_4', 'slide_5', 'slide_6', 'slide_7']
    
    for key in keys:
        if key in data:
            info = data[key]
            slide = prs.slides.add_slide(prs.slide_layouts[6]) 
            
            # 1. Barra Superior con el color detectado
            agregar_barra_superior(slide, info.get('titulo', ''), color_actual)
            
            # 2. Texto (Izquierda)
            # Aseguramos espacio después de la barra superior
            tb_body = slide.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(4.5), Inches(5.2))
            tf = tb_body.text_frame
            tf.word_wrap = True
            
            contenido = info.get('contenido') or info.get('puntos') or ""
            
            def add_p(text, bullet=False):
                p = tf.add_paragraph()
                p.text = str(text)
                p.font.size = Pt(18)
                p.space_after = Pt(8) 
                if bullet: p.text = "• " + str(text)

            if isinstance(contenido, list):
                for x in contenido: add_p(x, True)
            else:
                add_p(contenido)

            # 3. Imagen (Derecha) - Mejoramos el posicionamiento y tamaño
            desc = info.get('descripcion_imagen', '')
            if desc:
                img_bytes = obtener_imagen_ia(desc)
                if img_bytes:
                    try:
                        # La imagen ocupa un espacio similar al cuadro de texto de la derecha
                        # x, y, width, height (ajustado para dejar márgenes)
                        slide.shapes.add_picture(img_bytes, Inches(5.4), Inches(1.8), width=Inches(4.1), height=Inches(5.2))
                    except Exception as e_img:
                        print(f"Error al insertar imagen en slide {key}: {e_img}")
                        pass 

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer
