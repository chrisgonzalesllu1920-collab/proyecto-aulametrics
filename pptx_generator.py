import io
import json
import requests
from urllib.parse import quote
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

# Configuración de Colores
COLORES_TEMATICOS = {
    "Default": RGBColor(0, 51, 102)
}

def obtener_imagen_ia(descripcion_en_ingles):
    if not descripcion_en_ingles: return None
    try:
        # Prompt simple y codificado
        prompt = quote(descripcion_en_ingles)
        # URL directa
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=600&nologo=true"
        
        # Headers para evitar bloqueos y 20 segundos de espera
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            print(f"Error status code: {response.status_code}")
    except Exception as e:
        print(f"Error descargando imagen: {e}")
    return None

def agregar_barra_superior(slide, titulo_texto, color_tema):
    # Barra
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(1.4))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color_tema
    shape.line.fill.background()
    
    # Título (Borrar anterior si existe)
    if slide.shapes.title:
        try: slide.shapes.title.element.getparent().remove(slide.shapes.title.element)
        except: pass
        
    # Texto Título
    textbox = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(1))
    p = textbox.text_frame.paragraphs[0]
    p.text = titulo_texto
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.font.size = Pt(32)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

def crear_ppt_desde_data(json_texto):
    prs = Presentation()
    try:
        data = json.loads(json_texto.replace('```json', '').replace('```', '').strip())
    except:
        return None

    color_actual = COLORES_TEMATICOS["Default"]

    # Bucle para todas las slides (1 a 7)
    for i in range(1, 8):
        key = f"slide_{i}"
        if key in data:
            info = data[key]
            slide = prs.slides.add_slide(prs.slide_layouts[6]) # Blank
            
            # 1. Barra y Título
            agregar_barra_superior(slide, info.get('titulo', ''), color_actual)
            
            # 2. Subtítulo (Solo slide 1)
            if i == 1:
                tb = slide.shapes.add_textbox(Inches(1), Inches(4), Inches(8), Inches(1))
                p = tb.text_frame.paragraphs[0]
                p.text = info.get('subtitulo', '')
                p.alignment = PP_ALIGN.CENTER
                continue # Saltamos el resto para la portada

            # 3. Contenido Texto (Izquierda)
            tb = slide.shapes.add_textbox(Inches(0.5), Inches(1.6), Inches(4.5), Inches(5))
            tf = tb.text_frame
            tf.word_wrap = True
            contenido = info.get('contenido') or info.get('puntos') or ""
            
            if isinstance(contenido, list):
                for item in contenido:
                    p = tf.add_paragraph()
                    p.text = "• " + str(item)
                    p.font.size = Pt(18)
                    p.space_after = Pt(10)
            else:
                p = tf.add_paragraph()
                p.text = str(contenido)
                p.font.size = Pt(18)

            # 4. IMAGEN (Derecha) - CON DIAGNÓSTICO
            desc = info.get('descripcion_imagen', '')
            img_insertada = False
            
            if desc:
                img_bytes = obtener_imagen_ia(desc)
                if img_bytes:
                    try:
                        slide.shapes.add_picture(img_bytes, Inches(5.2), Inches(1.6), width=Inches(4.3))
                        img_insertada = True
                    except:
                        pass
            
            # SI FALLA LA IMAGEN, DIBUJAMOS CUADRO ROJO DE ERROR
            if not img_insertada and desc:
                shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.2), Inches(1.6), Inches(4.3), Inches(3))
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor(200, 200, 200) # Gris
                shape.text_frame.text = "⚠️ Error descargando imagen\n(Revisa conexión o firewall)"

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer
