"""
Conecta con tu cuenta de Gmail REAL (vía API oficial de Google), descarga
tus correos recientes, y los clasifica con SiCNN ya entrenado — usando
exactamente los mismos reportes (detalle + resumen) que ya tienes, ahora
en Excel.

Requiere haber configurado credentials.json primero (ver gmail_utils.py
para las instrucciones completas paso a paso).

USO en la terminal de VS Code:
    python analyze_gmail.py --max-correos 50 --modelo sicnn_final.keras --guardar-excel reporte_gmail.xlsx
"""
import argparse
import tensorflow as tf

from gmail_utils import autenticar, obtener_correos
from analyze_excel import (
    analizar, print_report, save_report_excel,
    generar_resumen, print_resumen, save_resumen_excel,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="sicnn_final.keras")
    parser.add_argument("--max-correos", type=int, default=50, help="Cantidad de correos recientes a analizar")
    parser.add_argument("--etiqueta", default="INBOX", help="Etiqueta de Gmail a leer (INBOX, SPAM, etc.)")
    parser.add_argument("--mostrar-legitimos", action="store_true")
    parser.add_argument("--guardar-excel", default="reporte_gmail.xlsx")
    args = parser.parse_args()

    print("Autenticando con tu cuenta de Gmail (se abrirá el navegador la primera vez)...")
    service = autenticar()

    df = obtener_correos(service, max_resultados=args.max_correos, etiqueta=args.etiqueta)

    if len(df) == 0:
        print("No se encontraron correos en esa etiqueta.")
        exit()

    modelo = tf.keras.models.load_model(args.modelo)

    reporte = analizar(df, modelo, "texto_correo", "asunto", "remitente", "id", "fecha_hora")
    print_report(reporte, mostrar_legitimos=args.mostrar_legitimos)

    save_report_excel(reporte, args.guardar_excel)

    resumen = generar_resumen(reporte)
    print_resumen(resumen)

    base, ext = args.guardar_excel.rsplit(".", 1) if "." in args.guardar_excel else (args.guardar_excel, "xlsx")
    save_resumen_excel(resumen, f"{base}_resumen.{ext}")
