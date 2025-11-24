import io
from pptx import Presentation
from pptx.util import Inches, Pt

def generar_ppt_prueba():
    """
    Genera un PowerPoint básico de prueba (Hola Mundo).
    Sirve para confirmar que el sistema puede crear archivos .pptx sin errores.
    """
    # 1. Crear una presentación vacía (usa la plantilla blanca por defecto)
    prs = Presentation()

    # 2. Agregar una diapositiva de Título (Layout 0 suele ser Título)
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)

    # 3. Escribir en los marcadores de posición (Título y Subtítulo)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    title.text = "¡Hola AulaMetrics!"
    subtitle.text = "Generación automática de PowerPoint exitosa."

    # 4. Guardar el archivo en memoria (Buffer)
    # Esto evita guardar archivos basura en el servidor
    ppt_buffer = io.BytesIO()
    prs.save(ppt_buffer)
    ppt_buffer.seek(0)

    return ppt_buffer
