import pandas as pd
import io 
from datetime import timedelta

def procesar_archivo(archivo):
    extension = archivo.name.split('.')[-1].lower()
    if extension == 'xlsx':
        return procesar_excel(archivo)
    elif extension == 'xml':
        return procesar_xml(archivo)
    else:
        raise ValueError("Formato de archivo no soportado")

def procesar_excel(archivo):
    # Leemos el archivo Excel
    df = pd.read_excel(archivo)
    print("Columnas encontradas en el archivo:", df.columns)

    df_preview = pd.read_excel(archivo, header=None)
    print(df_preview.head(10))  # Imprime las primeras 10 filas

    if 'Event Details' not in df.columns or 'Start Time' not in df.columns:
        raise ValueError("El archivo no contiene las columnas necesarias: 'Event Details' y 'Start Time'")

    # Filtramos las llamadas atendidas basándonos en la columna 'Answer Time'
    df_atendidas = df[df['Event Details'].notna()]

    # Convertimos 'Duración de llamada' a timedelta (asumiendo que está en segundos)
    df_atendidas['Duracion'] = pd.to_timedelta(df_atendidas['Start Time'], unit='s')

    # Cálculo del TMO
    tmo = df_atendidas['Duracion'].mean()

    # Resumen con los resultados
    resumen = {
        "TMO": tmo,
        "Total llamadas atendidas": len(df_atendidas),
        "Total llamadas": len(df),
    }

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Original', index=False)
        resumen_df = pd.DataFrame([resumen])
        resumen_df.to_excel(writer, sheet_name='Resumen', index=False)
    output.seek(0)

    return resumen, output


# Si usas XML
def procesar_xml(path_archivo):
    import xml.etree.ElementTree as ET
    tree = ET.parse(path_archivo)
    root = tree.getroot()

    # Aquí agregas la lógica para leer el XML y extraer datos
    # Por ejemplo:
    total_llamadas = sum(1 for elem in root.findall('.//llamada'))
    return {"Total llamadas": total_llamadas}
