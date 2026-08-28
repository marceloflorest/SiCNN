"""
Interfaz web LOCAL (con Flask) para analizar tus correos de Gmail con
SiCNN, y descargar los 2 informes en Excel directamente desde el
navegador, con un botón de descarga real.

No es una página en internet -- se ejecuta en tu propia computadora
(localhost) y solo tú puedes acceder a ella.

Requiere haber configurado credentials.json primero (ver gmail_utils.py).

USO en la terminal de VS Code:
    python web_app.py

Luego abre tu navegador en: http://127.0.0.1:5000
"""
import os
import uuid
import numpy as np
import tensorflow as tf
from flask import Flask, render_template_string, request, send_file, redirect, url_for, jsonify

from gmail_utils import autenticar, obtener_correos
from analyze_excel import analizar, generar_resumen, save_report_excel, save_resumen_excel
from text_to_image import texto_a_imagen
from indicadores import calcular_indicadores
from blockchain import Blockchain

app = Flask(__name__)

# Permite que Google Apps Script (dominio distinto) pueda llamar a esta API
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

MODELO_PATH = "sicnn_final.keras"
CARPETA_SALIDA = "reportes_web"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

BLOCKCHAIN_FILE = "blockchain_resultados.json"


def obtener_blockchain():
    if os.path.exists(BLOCKCHAIN_FILE):
        return Blockchain.cargar_json(BLOCKCHAIN_FILE)
    return Blockchain()

_modelo_cache = None


def obtener_modelo():
    global _modelo_cache
    if _modelo_cache is None:
        _modelo_cache = tf.keras.models.load_model(MODELO_PATH)
    return _modelo_cache

HTML_BASE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Detector de Phishing - SiCNN</title>
<style>
  body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 40px; }
  .card { background: white; max-width: 640px; margin: 0 auto; padding: 32px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
  h1 { color: #1a1a2e; font-size: 22px; margin-bottom: 4px; }
  .subtitulo { color: #666; margin-bottom: 24px; font-size: 14px; }
  label { display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 14px; }
  input[type=number] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; margin-bottom: 20px; box-sizing: border-box; }
  button, .boton { background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 15px; cursor: pointer; text-decoration: none; display: inline-block; }
  button:hover, .boton:hover { background: #1d4ed8; }
  .resultado { margin-top: 24px; padding: 20px; background: #f0f9f4; border-radius: 8px; border: 1px solid #c8e6d0; }
  .resultado h2 { margin-top: 0; font-size: 17px; color: #1a1a2e; }
  .stat { font-size: 14px; margin: 4px 0; color: #333; }
  .descargas { margin-top: 16px; display: flex; gap: 10px; }
  .aviso { font-size: 13px; color: #888; margin-top: 16px; }
</style>
</head>
<body>
<div class="card">
  <h1>Detector de Phishing - SiCNN</h1>
  <p class="subtitulo">Analiza tus correos reales de Gmail y descarga los informes en Excel</p>
  {{ contenido|safe }}
</div>
</body>
</html>
"""

HTML_FORM = """
<form method="POST" action="/analizar">
  <label for="max_correos">Cantidad de correos recientes a analizar</label>
  <input type="number" id="max_correos" name="max_correos" value="50" min="1" max="500" required>
  <button type="submit">Analizar mis correos de Gmail</button>
</form>
<p class="aviso">La primera vez se abrirá una ventana pidiendo autorizar el acceso de solo lectura a tu Gmail.</p>
"""

HTML_RESULTADO = """
<div class="resultado">
  <h2>Análisis completado</h2>
  <p class="stat">Total de correos analizados: <b>{{ total }}</b></p>
  <p class="stat">Legítimos: <b>{{ legitimos }}</b> ({{ pct_legitimos }}%)</p>
  <p class="stat">Phishing: <b>{{ phishing }}</b> ({{ pct_phishing }}%)</p>
  <div class="descargas">
    <a class="boton" href="/descargar/{{ archivo_detalle }}">Descargar informe detallado (Excel)</a>
    <a class="boton" href="/descargar/{{ archivo_resumen }}">Descargar resumen (Excel)</a>
  </div>
</div>
<p><a href="/">Analizar de nuevo</a></p>
"""


@app.route("/")
def home():
    return render_template_string(HTML_BASE, contenido=HTML_FORM)


@app.route("/analizar", methods=["POST"])
def analizar_gmail():
    max_correos = int(request.form.get("max_correos", 50))

    service = autenticar()
    df = obtener_correos(service, max_resultados=max_correos)

    if len(df) == 0:
        return render_template_string(HTML_BASE, contenido="<p>No se encontraron correos.</p><a href='/'>Volver</a>")

    modelo = tf.keras.models.load_model(MODELO_PATH)
    reporte = analizar(df, modelo, "texto_correo", "asunto", "remitente", "id", "fecha_hora")
    resumen = generar_resumen(reporte)

    archivo_detalle = "reporte_gmail.xlsx"
    archivo_resumen = "reporte_gmail_resumen.xlsx"
    save_report_excel(reporte, os.path.join(CARPETA_SALIDA, archivo_detalle))
    save_resumen_excel(resumen, os.path.join(CARPETA_SALIDA, archivo_resumen))

    contenido = render_template_string(
        HTML_RESULTADO,
        total=resumen["total"],
        legitimos=resumen["total"] - int(round(resumen["total"] * resumen["pct_phishing"] / 100)),
        phishing=int(round(resumen["total"] * resumen["pct_phishing"] / 100)),
        pct_legitimos=f"{resumen['pct_legitimos']:.1f}",
        pct_phishing=f"{resumen['pct_phishing']:.1f}",
        archivo_detalle=archivo_detalle,
        archivo_resumen=archivo_resumen,
    )
    return render_template_string(HTML_BASE, contenido=contenido)


@app.route("/descargar/<nombre_archivo>")
def descargar(nombre_archivo):
    ruta = os.path.join(CARPETA_SALIDA, nombre_archivo)
    return send_file(ruta, as_attachment=True)


# ============================================================
# API para el COMPLEMENTO DE GMAIL (Google Apps Script)
# El complemento lee los correos directamente desde Gmail y
# envía aquí el texto para clasificar -- esta API no accede a
# Gmail por su cuenta, solo recibe texto y devuelve el resultado.
# ============================================================

@app.route("/api/analizar", methods=["POST", "OPTIONS"])
def api_analizar():
    """
    Recibe uno o varios correos ya extraídos por el complemento de Gmail
    y los clasifica. Genera también un Excel descargable, identificado
    por un token único que el complemento puede usar después para el
    botón "Descargar informe".

    Formato esperado (JSON):
    {
        "correos": [
            {"id": "...", "fecha_hora": "...", "asunto": "...", "remitente": "...", "texto_correo": "..."}
        ]
    }
    """
    if request.method == "OPTIONS":
        return "", 204

    datos = request.get_json(force=True)
    correos = datos.get("correos", [])

    if not correos:
        return jsonify({"error": "No se recibieron correos"}), 400

    modelo = obtener_modelo()
    resultados = []
    for correo in correos:
        asunto = correo.get("asunto", "")
        remitente = correo.get("remitente", "")
        texto = correo.get("texto_correo", "")

        imagen = texto_a_imagen(asunto, remitente, texto)
        imagen = np.expand_dims(imagen, axis=0)
        proba = float(modelo.predict(imagen, verbose=0)[0][0])
        clasificacion = "PHISHING" if proba >= 0.5 else "LEGÍTIMO"
        indicadores = calcular_indicadores(remitente, asunto, texto)

        resultados.append({
            "id": correo.get("id", ""),
            "fecha_hora": correo.get("fecha_hora", ""),
            "remitente": remitente,
            "asunto": asunto,
            "clasificacion": clasificacion,
            "probabilidad_phishing": round(proba * 100, 2),
            "indicadores": indicadores,
        })

    # Generar el Excel descargable y guardarlo con un token único
    import pandas as pd
    df_resultados = pd.DataFrame(resultados)
    token = uuid.uuid4().hex[:12]
    nombre_archivo = f"reporte_gmail_{token}.xlsx"
    df_resultados.to_excel(os.path.join(CARPETA_SALIDA, nombre_archivo), index=False, sheet_name="Detalle")

    total = len(resultados)
    phishing_count = sum(1 for r in resultados if r["clasificacion"] == "PHISHING")

    # --- Registro en la blockchain: UN BLOQUE POR CADA CORREO (legítimo o phishing) ---
    blockchain = obtener_blockchain()
    bloques_creados = []
    for r in resultados:
        bloque = blockchain.registrar_resultado(algoritmo="SICNN", datos={
            "origen": "complemento_gmail",
            "id_correo": r["id"],
            "fecha_hora": r["fecha_hora"],
            "remitente": r["remitente"],
            "asunto": r["asunto"],
            "clasificacion": r["clasificacion"],
            "probabilidad_phishing": r["probabilidad_phishing"],
            "indicadores": r["indicadores"],
        })
        bloques_creados.append({"indice": bloque.indice, "hash": bloque.hash_propio})

    blockchain.guardar_json(BLOCKCHAIN_FILE)
    es_valida, _ = blockchain.verificar_integridad()

    return jsonify({
        "token": token,
        "archivo": nombre_archivo,
        "total": total,
        "phishing": phishing_count,
        "legitimos": total - phishing_count,
        "resultados": resultados,
        "blockchain": {
            "bloques_creados": len(bloques_creados),
            "primer_indice": bloques_creados[0]["indice"] if bloques_creados else None,
            "ultimo_indice": bloques_creados[-1]["indice"] if bloques_creados else None,
            "cadena_valida": es_valida,
        },
    })


if __name__ == "__main__":
    print("Abre tu navegador en: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
