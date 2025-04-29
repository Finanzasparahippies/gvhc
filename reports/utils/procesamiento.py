import pandas as pd
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

    # Filtramos las llamadas atendidas basándonos en la columna 'Answer Time'
    df_atendidas = df[df['Answer Time'].notna()]

    # Convertimos 'Duración de llamada' a timedelta (asumiendo que está en segundos)
    df_atendidas['Duracion'] = pd.to_timedelta(df_atendidas['Duración de llamada'], unit='s')

    # Cálculo del TMO
    tmo = df_atendidas['Duracion'].mean()

    # Resumen con los resultados
    resumen = {
        "TMO": tmo,
        "Total llamadas atendidas": len(df_atendidas),
        "Total llamadas": len(df),
    }

    return resumen


# Si usas XML
def procesar_xml(path_archivo):
    import xml.etree.ElementTree as ET
    tree = ET.parse(path_archivo)
    root = tree.getroot()

    # Aquí agregas la lógica para leer el XML y extraer datos
    # Por ejemplo:
    total_llamadas = sum(1 for elem in root.findall('.//llamada'))
    return {"Total llamadas": total_llamadas}
