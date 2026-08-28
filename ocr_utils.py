"""
Extracción de texto desde una imagen (captura de pantalla de un correo)
usando OCR (Tesseract), para poder clasificarla con AlexNet.
"""
from PIL import Image
import pytesseract


def extract_text_from_image(image_path: str, lang: str = "spa+eng") -> str:
    """
    Extrae todo el texto visible de una imagen.
    lang: idiomas para el OCR. Si 'spa' no está instalado, reintenta con 'eng'.
    """
    img = Image.open(image_path)
    try:
        text = pytesseract.image_to_string(img, lang=lang)
    except pytesseract.TesseractError:
        text = pytesseract.image_to_string(img, lang="eng")
    return text.strip()
