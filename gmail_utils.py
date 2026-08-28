"""
Conector a Gmail vía API oficial de Google, para leer correos reales de
tu cuenta PERSONAL y clasificarlos con el modelo ya entrenado.

===========================================================================
CONFIGURACIÓN NECESARIA (una sola vez, ~15 minutos)
===========================================================================
1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo (arriba a la izquierda, "Seleccionar proyecto" -> "Proyecto nuevo")
3. Ve a "APIs y servicios" > "Biblioteca" > busca "Gmail API" > Habilitar
4. Ve a "APIs y servicios" > "Pantalla de consentimiento OAuth"
   - Tipo de usuario: Externo
   - Completa el nombre de la app (ej. "Detector Phishing Tesis") y tu correo
   - En "Usuarios de prueba", agrega TU PROPIO correo de Gmail
5. Ve a "Credenciales" > "Crear credenciales" > "ID de cliente de OAuth"
   - Tipo de aplicación: "Aplicación de escritorio"
   - Descarga el archivo JSON resultante
6. Renombra ese archivo a "credentials.json" y colócalo en esta misma
   carpeta del proyecto (junto a train.py, analyze_excel.py, etc.)

La PRIMERA vez que corras analyze_gmail.py, se abrirá tu navegador
pidiendo iniciar sesión con tu cuenta de Gmail y autorizar acceso de
SOLO LECTURA (no puede enviar, borrar, ni modificar nada). Tras
autorizar una vez, se guarda "token.json" para no repetir el login.
===========================================================================
"""
import os
import base64
import pandas as pd
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Acceso de SOLO LECTURA -- el software nunca puede enviar, borrar ni
# modificar correos, solo leerlos para clasificarlos.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def autenticar():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "No se encontró 'credentials.json' en esta carpeta.\n"
                    "Sigue las instrucciones al inicio de gmail_utils.py para "
                    "generarlo desde Google Cloud Console (Gmail API + credenciales OAuth)."
                )
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _extraer_texto(payload):
    """Extrae el texto plano del cuerpo del correo (maneja mensajes simples y multipart)."""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part["body"].get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            if "parts" in part:
                texto = _extraer_texto(part)
                if texto:
                    return texto
    else:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""


def obtener_correos(service, max_resultados=50, etiqueta="INBOX"):
    """
    Descarga los correos más recientes de Gmail y los devuelve como
    DataFrame con las MISMAS columnas que usa el resto del software:
    id, fecha_hora, asunto, remitente, texto_correo.
    """
    resultados = service.users().messages().list(
        userId="me", labelIds=[etiqueta], maxResults=max_resultados
    ).execute()
    mensajes = resultados.get("messages", [])

    print(f"Se encontraron {len(mensajes)} correos. Descargando contenido...")

    registros = []
    for m in mensajes:
        msg = service.users().messages().get(userId="me", id=m["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

        asunto = headers.get("Subject", "(sin asunto)")
        remitente = headers.get("From", "(desconocido)")
        fecha_ms = int(msg.get("internalDate", 0))
        fecha_hora = datetime.fromtimestamp(fecha_ms / 1000).strftime("%d/%m/%Y %H:%M")
        texto = _extraer_texto(msg["payload"])

        registros.append({
            "id": m["id"],
            "fecha_hora": fecha_hora,
            "asunto": asunto,
            "remitente": remitente,
            "texto_correo": texto,
        })

    return pd.DataFrame(registros)
