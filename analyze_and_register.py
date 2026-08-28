"""
Analiza el Excel con SiCNN y registra el resultado en la blockchain
(SHA-256), igual que en phishing_detector.

USO:
    python analyze_and_register.py --input "ruta\\a\\tu_excel.xlsx"
"""
import argparse
import pandas as pd
import tensorflow as tf

from analyze_excel import analizar, print_report, save_report_excel, generar_resumen, print_resumen, save_resumen_excel, ALGORITMO
from blockchain import Blockchain

BLOCKCHAIN_FILE = "blockchain_resultados.json"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--modelo", default="sicnn_final.keras")
    parser.add_argument("--sheet", default=0)
    parser.add_argument("--col-texto", default="texto_correo")
    parser.add_argument("--col-asunto", default="asunto")
    parser.add_argument("--col-remitente", default="remitente")
    parser.add_argument("--col-id", default="id")
    parser.add_argument("--col-fecha", default="fecha_hora")
    parser.add_argument("--mostrar-legitimos", action="store_true")
    parser.add_argument("--guardar-excel", default="reporte.xlsx")
    args = parser.parse_args()

    df = pd.read_excel(args.input, sheet_name=args.sheet)
    modelo = tf.keras.models.load_model(args.modelo)

    reporte = analizar(df, modelo, args.col_texto, args.col_asunto, args.col_remitente, args.col_id, args.col_fecha)
    print_report(reporte, mostrar_legitimos=args.mostrar_legitimos)

    save_report_excel(reporte, args.guardar_excel)

    resumen_ejecutivo = generar_resumen(reporte)
    print_resumen(resumen_ejecutivo)

    base, ext = args.guardar_excel.rsplit(".", 1) if "." in args.guardar_excel else (args.guardar_excel, "xlsx")
    save_resumen_excel(resumen_ejecutivo, f"{base}_resumen.{ext}")

    phishing = reporte[reporte["clasificacion"] == "PHISHING"]
    legitimos = reporte[reporte["clasificacion"] == "LEGÍTIMO"]

    resumen_blockchain = {
        "total_analizado": len(reporte),
        "legitimos": len(legitimos),
        "phishing": len(phishing),
        "remitentes_phishing": sorted(phishing["remitente"].unique().tolist()),
    }

    blockchain = Blockchain()
    bloque = blockchain.registrar_resultado(algoritmo=ALGORITMO.upper(), datos=resumen_blockchain)
    blockchain.guardar_json(BLOCKCHAIN_FILE)

    es_valida, corruptos = blockchain.verificar_integridad()

    print(f"\n{'='*50}")
    print("REGISTRO EN BLOCKCHAIN")
    print(f"{'='*50}")
    print(f"Algoritmo: {ALGORITMO}")
    print(f"Bloque creado: #{bloque.indice}")
    print(f"Hash del bloque: {bloque.hash_propio}")
    print(f"Hash del bloque anterior: {bloque.hash_anterior}")
    print(f"Integridad de la cadena: {'VÁLIDA' if es_valida else 'CORROMPIDA'}")
    print(f"Blockchain guardada en: {BLOCKCHAIN_FILE}")
