# reports/send_report.py

import pandas as pd
from datetime import datetime
import requests

def send_teams_report():
    # 1. Leer los datos
    df_calls = pd.read_excel("ruta/a/tu/aht_calls.xlsx", sheet_name="AHT")
    df_paces = pd.read_excel("ruta/a/tu/aht_calls.xlsx", sheet_name="PACES")

    # 2. Convertir a HTML sin índice ni bordes
    html_calls = df_calls.to_html(index=False, border=0)
    html_paces = df_paces.to_html(index=False, border=0)

    # 3. Construir el mensaje
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    message = f"""
    <div>
        <h3><strong>AHT/CALLS – {now} H M O / M X L I –</strong></h3>
        {html_calls}
        <h3><strong>PACE'S – {now} H M O / M X L I –</strong></h3>
        {html_paces}
        <p><strong>Keep doing like that! 💪</strong></p>
    </div>
    """

    # 4. Enviar a Teams
    webhook_url = "https://outlook.office.com/webhook/..."  # ← reemplaza con el tuyo
    payload = {
        "text": "Daily Metrics Report",
        "attachments": [{
            "contentType": "html",
            "content": message
        }]
    }

    response = requests.post(webhook_url, json=payload)

    print(f"Mensaje enviado. Status: {response.status_code}")
