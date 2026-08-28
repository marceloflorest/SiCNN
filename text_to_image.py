"""
Convierte el texto de un correo (asunto + remitente + texto_correo) en una
representación de IMAGEN numérica, para que pueda ser procesada por una
CNN (AlexNet o SiCNN), que están diseñadas para trabajar con píxeles.

Técnica: hashing de palabras (HashingVectorizer) → vector de frecuencias →
se reordena como una matriz cuadrada → se normaliza a escala de grises
(0-255) → se replica en 3 canales (RGB) → se redimensiona al tamaño de
entrada de la CNN (224x224x3).

Esto es una solución PROVISIONAL mientras no se cuenta con capturas de
pantalla reales. Cuando existan imágenes reales, se reemplaza esta función
por la carga directa de la imagen (ver train.py, sección comentada) — el
resto del pipeline (arquitectura de la CNN, blockchain, reporte) no cambia.
"""
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

MATRIZ_LADO = 56          # 56 x 56 = 3136 "buckets" de hashing (56*4 = 224)
IMG_SIZE = 224             # tamaño de entrada esperado por AlexNet/SiCNN

_vectorizador = HashingVectorizer(
    n_features=MATRIZ_LADO * MATRIZ_LADO,
    alternate_sign=False,
    norm=None,
)


def _resize_nearest(matriz, nuevo_lado):
    """Redimensiona una matriz 2D usando repetición (nearest neighbor), sin dependencias extra."""
    factor = nuevo_lado // matriz.shape[0]
    return np.kron(matriz, np.ones((factor, factor)))


def texto_a_imagen(asunto: str, remitente: str, texto: str) -> np.ndarray:
    """Convierte un correo en un array (224, 224, 3) con valores 0-1."""
    contenido = f"{asunto} {remitente} {texto}"
    vector = _vectorizador.transform([contenido]).toarray()[0]

    matriz = vector.reshape(MATRIZ_LADO, MATRIZ_LADO)

    maximo = matriz.max()
    if maximo > 0:
        matriz = (matriz / maximo) * 255.0

    matriz_grande = _resize_nearest(matriz, IMG_SIZE)
    imagen = np.stack([matriz_grande] * 3, axis=-1)  # 3 canales (RGB)
    return (imagen / 255.0).astype(np.float32)
