import pandas as pd
import numpy as np
import unicodedata

NIVELES_LOGRO = ['AD', 'A', 'B', 'C']
GENERAL_SHEET_NAME = 'Generalidades' 

def get_level_counts(series):
    """
    Cuenta la frecuencia de los niveles de logro en una serie, 
    filtrando estrictamente por 'AD', 'A', 'B', 'C' para ignorar descripciones y vacíos.
    """
    # 1. Filtra la serie para incluir solo los niveles de logro válidos (AD, A, B, C)
    valid_series = series[series.isin(NIVELES_LOGRO)]
    
    # 2. Cuenta la frecuencia
    counts = valid_series.value_counts().reindex(NIVELES_LOGRO, fill_value=0).to_dict()
    
    # 3. El total evaluado es la cuenta de valores válidos
    total_evaluados = valid_series.shape[0]
    
    return {'conteo_niveles': counts, 'total_evaluados': total_evaluados}

def clean_competencia_name(name: str) -> str:
    """Limpia el prefijo 'XX = ' del nombre de la competencia."""
    if pd.isna(name):
        return "Competencia Desconocida"
    name_str = str(name).strip()
    if '=' in name_str:
        # Esto quita el prefijo '01 = '
        return name_str.split('=', 1)[1].strip()
    return name_str.strip()

def extract_general_data(excel_file):
    """
    Extrae el Grado (H10) y el Nivel (H5) de la hoja 'Generalidades'.
    """
    try:
        df_generalidades = pd.read_excel(
            excel_file, 
            sheet_name=GENERAL_SHEET_NAME, 
            header=None, 
            nrows=10, 
            usecols=range(8)
        )
        
        grado = df_generalidades.iloc[9, 7] 
        nivel = df_generalidades.iloc[4, 7]
        
        grado_str = str(grado).strip() if pd.notna(grado) else "Grado Desconocido"
        nivel_str = str(nivel).strip() if pd.notna(nivel) else "Nivel Desconocido"

        return {
            'grado': grado_str,
            'nivel': nivel_str
        }

    except Exception as e:
        return {
            'grado': f'Error al leer el grado ({str(e)})',
            'nivel': f'Error al leer el nivel ({str(e)})',
            'error_details': str(e)
        }

def analyze_data(excel_file, sheet_names):
    """
    Procesa las hojas seleccionadas basándose en la estructura compleja del Excel.
    """
    analisis_results = {}
    
    general_data = extract_general_data(excel_file)
    
    # El for debe estar al mismo nivel que general_data (sin espacios extras al inicio)
    for sheet_name in sheet_names:
        print(f"DEBUG - Hoja detectada: '{sheet_name}' (longitud: {len(sheet_name)})")  # ← print normal
        
        # Normalización ultra-robusta
        import unicodedata
        sheet_normalized = ''.join(c for c in unicodedata.normalize('NFD', sheet_name) 
                                   if unicodedata.category(c) != 'Mn').lower().strip()
        
        print(f"DEBUG - Normalizado: '{sheet_normalized}' (comparando con 'comentarios')")
        
        if sheet_normalized == "comentarios":
            print(f"DEBUG - Ignorando hoja: {sheet_name}")
            analisis_results[sheet_name] = {
                'error': f"Hoja ignorada: '{sheet_name}' es la hoja de comentarios y no contiene competencias.",
                'generalidades': general_data,
                'competencias': {}
            }
            continue
           

        try:
            df_full = pd.read_excel(excel_file, sheet_name=sheet_name, header=None) 
            max_cols = df_full.shape[1] 

            # A. Identificar límites de estudiantes (Columna A/índice 0)
            is_student_row = df_full.iloc[:, 0].apply(lambda x: pd.notna(x) and isinstance(x, (int, float)) and x == int(x) and x > 0)
            last_student_row_index = df_full[is_student_row].index.max()

            # El primer estudiante está en la Fila 3 (índice 2)
            data_start_row_index = 2 
            
            # El último estudiante es la fila máxima con un número en Columna A
            end_data_row_index = int(last_student_row_index) if pd.notna(last_student_row_index) else 32
            
            # La primera fila con el nombre de la competencia (ej: '01 = ...')
            comp_name_start_row_index = end_data_row_index + 4
            
            # B. Extraer Nombres de Competencias (en Columna B, índice 1)
            competencias_raw = df_full.iloc[comp_name_start_row_index:, 1]
            competencias_list = []
            
            for idx, val in competencias_raw.head(15).items():
                if pd.notna(val) and isinstance(val, str) and '=' in val and val.strip().lower().startswith(('01', '02', '03', '04', '05', '06', '07', '08', '09', '10')):
                    competencias_list.append((idx, val))
            
            if not competencias_list:
                 raise ValueError("No se pudieron identificar los nombres de las competencias en el rango esperado (Columna B).")

            
            # C. Analizar cada Competencia: Patrón D, F, H, J...
            competencias_data = {}
            
            # *** CORRECCIÓN CRÍTICA: La primera nota (NL) está en Columna D (índice 3) ***
            START_NOTE_COLUMN_INDEX = 3 
            
            # *** CORRECCIÓN CRÍTICA: El salto es de +2 (para D -> F -> H...) ***
            JUMP_SIZE = 2
            
            for i, (row_idx, comp_name_full) in enumerate(competencias_list):
                
                # Cálculo de la columna de nota (NL): 3 + (i * 2)
                note_col_index = START_NOTE_COLUMN_INDEX + (i * JUMP_SIZE) 
                
                # VERIFICACIÓN CRÍTICA
                if note_col_index >= max_cols:
                    break
                
                # Extraemos la serie de notas:
                notas_series = df_full.iloc[data_start_row_index : end_data_row_index + 1, note_col_index]

                # Analizar la serie de notas (la función get_level_counts es estricta)
                counts = get_level_counts(
                    notas_series.astype(str).str.strip().str.upper()
                )
                
                # Almacenar datos
                comp_name_clean = clean_competencia_name(comp_name_full)
                
                competencias_data[comp_name_full] = {
                    'conteo_niveles': counts['conteo_niveles'],
                    'total_evaluados': counts['total_evaluados'],
                    'nombre_limpio': comp_name_clean
                }
            
            # Guardar el resultado para esta hoja
            analisis_results[sheet_name] = {
                'generalidades': general_data,
                'competencias': competencias_data
            }

        except Exception as e:
            analisis_results[sheet_name] = {
                'error': f"Error al procesar la hoja '{sheet_name}': {e}",
                'generalidades': general_data,
                'competencias': {}
            }
            

    return analisis_results






