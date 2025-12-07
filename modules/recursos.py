import streamlit as st
import os

def recursos_page():
    """
    Renderiza la interfaz completa del Banco de Recursos Pedagógicos.
    
    Esta función es llamada por app.py cuando la variable de estado 'pagina' es "Recursos".
    Mantiene la estructura de dos columnas y la lógica de descarga de archivos
    existentes en la carpeta 'recursos/'.
    """
    
    st.header("📂 Banco de Recursos Pedagógicos")
    st.markdown("Descarga formatos, plantillas y guías útiles para tu labor docente.")
    st.divider()

    # Se mantiene la estructura de columnas original
    col_formatos, col_guias = st.columns(2)

    with col_formatos:
        st.subheader("📝 Formatos Editables")
        st.info("Plantillas en Word y Excel listas para usar.")
        
        # RECURSO 1: SECUNDARIA
        ruta_archivo_1 = "recursos/Registro automatizado nivel secundario.xlsm" 
        if os.path.exists(ruta_archivo_1):
            with open(ruta_archivo_1, "rb") as file:
                st.download_button(
                    label="📥 Descargar Registro Automatizado - Secundaria (Excel)",
                    data=file,
                    file_name="Registro_Secundaria.xlsm",
                    mime="application/vnd.ms-excel.sheet.macroEnabled.12", 
                    use_container_width=True
                )
        else:
            st.caption(f"❌ Archivo no encontrado: {ruta_archivo_1}")

        st.write("")
        
        # RECURSO 2: PRIMARIA
        ruta_archivo_2 = "recursos/Registro automatizado nivel primario.xlsm" 
        if os.path.exists(ruta_archivo_2):
            with open(ruta_archivo_2, "rb") as file:
                st.download_button(
                    label="📥 Descargar Registro Automatizado - Primaria (Excel)",
                    data=file,
                    file_name="Registro_Primaria.xlsm",
                    mime="application/vnd.ms-excel.sheet.macroEnabled.12", 
                    use_container_width=True
                )
        else:
            st.caption(f"❌ Archivo no encontrado: {ruta_archivo_2}")

        st.write("")
        
        # RECURSO 3: CALENDARIO
        ruta_archivo_3 = "recursos/calendario_2025.pdf" 
        if os.path.exists(ruta_archivo_3):
            with open(ruta_archivo_3, "rb") as file:
                st.download_button("📥 Descargar Calendario Cívico (PDF)", file, "Calendario_Civico_2025.pdf", "application/pdf", use_container_width=True)
        else:
            st.caption("❌ Archivo 'calendario_2025.pdf' no disponible.")
            
    # Agregamos la columna derecha (col_guias) para mantener la estructura visual.
    with col_guias:
        st.subheader("📚 Guías y Documentos")
        st.info("Próximamente: Guías de planificación y tutoriales.")
        st.warning("¡Esta sección se llenará con más contenido en la próxima actualización!")
        st.write("")
