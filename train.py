"""
Entrena SiCNN usando tu dataset de correos (Excel), convirtiendo cada
correo en una representación de imagen (ver text_to_image.py).

Las etiquetas (phishing / legítimo) se generan a partir del dominio del
remitente: cualquier correo que NO venga del dominio institucional se
considera phishing. Ajusta LEGIT_DOMAIN si tu dominio institucional es
distinto.

USO:
    python train.py --input "ruta\\a\\tu_excel.xlsx" --epochs 5

CUANDO TENGAS IMÁGENES REALES (capturas de pantalla):
Reemplaza la función cargar_dataset() para que cargue imágenes desde
carpetas (data/images/train/phishing, data/images/train/legitimate) con
tf.keras.utils.image_dataset_from_directory, en vez de convertir texto.
El resto del script (arquitectura, entrenamiento) no cambia.
"""
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

from models import build_sicnn, INPUT_SHAPE
from text_to_image import texto_a_imagen

LEGIT_DOMAIN = "essalud.gob.pe"


def cargar_dataset(ruta_excel, sheet, col_texto, col_asunto, col_remitente):
    df = pd.read_excel(ruta_excel, sheet_name=sheet)

    df["label"] = df[col_remitente].apply(
        lambda x: 0 if isinstance(x, str) and x.split("@")[-1] == LEGIT_DOMAIN else 1
    )

    print("Generando imágenes a partir del texto de cada correo...")
    X = np.array([
        texto_a_imagen(row[col_asunto], row[col_remitente], row[col_texto])
        for _, row in df.iterrows()
    ], dtype=np.float16)  # float16 reduce a la mitad el uso de memoria
    y = df["label"].values.astype(np.float32)

    return X, y


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Ruta al Excel de correos")
    parser.add_argument("--sheet", default=0)
    parser.add_argument("--col-texto", default="texto_correo")
    parser.add_argument("--col-asunto", default="asunto")
    parser.add_argument("--col-remitente", default="remitente")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()

    X, y = cargar_dataset(args.input, args.sheet, args.col_texto, args.col_asunto, args.col_remitente)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Entrenamiento: {len(X_train)} correos | Validación: {len(X_val)} correos")

    # --- Balanceo de datos ---
    # El dataset suele estar muy desbalanceado (pocos phishing vs muchos
    # legítimos). Sin esto, el modelo tiende a predecir casi siempre
    # "legítimo" y aun así tener accuracy alta, sin aprender el patrón real.
    clases = np.unique(y_train)
    pesos = compute_class_weight(class_weight="balanced", classes=clases, y=y_train)
    # Se limita el peso máximo a 10 para evitar que el desbalance extremo
    # (ej. 100 phishing vs 5200 legítimos) empuje al modelo a predecir
    # casi siempre "phishing" sin aprender un patrón real.
    pesos = np.clip(pesos, a_min=None, a_max=10.0)
    class_weight = {int(c): float(p) for c, p in zip(clases, pesos)}
    print(f"Pesos de balanceo por clase (0=legítimo, 1=phishing), limitados a máx. 10: {class_weight}")

    model = build_sicnn(input_shape=INPUT_SHAPE, num_classes=1)
    model.compile(optimizer=Adam(learning_rate=1e-4), loss="binary_crossentropy", metrics=["accuracy"])
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=32,
        class_weight=class_weight,
        callbacks=callbacks,
    )

    model.save("sicnn_final.keras")
    print("\nModelo guardado en sicnn_final.keras")
