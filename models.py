"""
Arquitectura SiCNN (Scale-Invariant CNN) para clasificar capturas de
pantalla de páginas web o correos como phishing / legítimo.

Cada "columna" procesa la imagen a una escala distinta usando el MISMO
backbone convolucional (pesos compartidos); luego se combinan las
características de todas las columnas para clasificar. Esto la hace más
robusta a capturas en distintas resoluciones.

Referencia: Xu et al., "Scale-Invariant Convolutional Neural Networks"
(2014), adaptada aquí de forma simplificada para clasificación binaria.
"""
from tensorflow.keras import layers, models

INPUT_SHAPE = (224, 224, 3)


def _shared_backbone(input_shape):
    inp = layers.Input(shape=input_shape)
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(inp)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(64, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(128, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(128, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Flatten()(x)
    x = layers.Dense(128, activation="relu")(x)
    return models.Model(inp, x, name="shared_backbone")


def build_sicnn(input_shape=INPUT_SHAPE, num_classes=1, scales=(1.0, 0.75, 0.5)):
    backbone = _shared_backbone(input_shape)

    original_input = layers.Input(shape=input_shape)
    h, w = input_shape[0], input_shape[1]

    column_outputs = []
    for scale in scales:
        target_h, target_w = int(h * scale), int(w * scale)
        scaled = layers.Resizing(target_h, target_w)(original_input)
        resized_back = layers.Resizing(h, w)(scaled)
        column_outputs.append(backbone(resized_back))

    merged = layers.Concatenate()(column_outputs) if len(column_outputs) > 1 else column_outputs[0]

    x = layers.Dense(256, activation="relu")(merged)
    x = layers.Dropout(0.5)(x)

    activation = "sigmoid" if num_classes == 1 else "softmax"
    out = layers.Dense(num_classes, activation=activation)(x)

    return models.Model(original_input, out, name="SiCNN")
