"""
Detecta indicadores específicos de irregularidad en un correo: dominio
sospechoso, URL/llamado a la acción, archivo adjunto, imagen adjunta, y
asunto vacío/anómalo.

Cada indicador es una regla INDEPENDIENTE de la clasificación general del
modelo — no repite la misma lógica de etiquetado, sino que busca patrones
adicionales que expliquen POR QUÉ un correo se ve sospechoso.

Se usan únicamente para el reporte (solo se muestran en correos marcados
como PHISHING); los legítimos no llevan indicadores.
"""
import re

DOMINIO_PALABRAS_SOSPECHOSAS = [
    "banco", "alerta", "seguro", "verificacion", "verificación",
    "premio", "loteria", "lotería", "soporte", "cuenta", "falso",
]
TLDS_SOSPECHOSOS = [".xyz", ".online", ".info", ".top", ".club", ".gq", ".tk", ".ml"]

PALABRAS_URL_ACCION = [
    "haga clic", "haz clic", "verifique aqui", "verifique aquí",
    "acceda ahora", "confirme su cuenta", "actualizacion", "actualización",
    "verificacion", "verificación", "expiracion", "expiración",
]

PALABRAS_ARCHIVO = [
    "adjunto", "descargue", "descargar", "abra el archivo", "documento adjunto",
]
EXTENSIONES_DOCUMENTO = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".zip", ".exe", ".scr", ".js", ".bat"]
EXTENSIONES_IMAGEN = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]


def detectar_indicador_correo(remitente: str) -> int:
    """Dominio con señales típicas de suplantación (palabras de alarma, TLD raro, guiones, dígitos)."""
    remitente = str(remitente).lower()
    dominio = remitente.split("@")[-1] if "@" in remitente else remitente

    if any(p in dominio for p in DOMINIO_PALABRAS_SOSPECHOSAS):
        return 1
    if any(dominio.endswith(t) for t in TLDS_SOSPECHOSOS):
        return 1
    if "-" in dominio:
        return 1
    parte_nombre = dominio.split(".")[0] if "." in dominio else dominio
    if re.search(r"\d", parte_nombre):
        return 1
    return 0


def detectar_indicador_url(asunto: str, texto: str) -> int:
    """Enlace literal o lenguaje típico de llamado a la acción/urgencia."""
    contenido = f"{asunto} {texto}".lower()
    if "http" in contenido or "www." in contenido:
        return 1
    if any(p in contenido for p in PALABRAS_URL_ACCION):
        return 1
    return 0


def detectar_indicador_archivo(texto: str) -> int:
    """Menciones de documento adjunto (pdf, docx, etc.) — no incluye imágenes."""
    texto_lower = str(texto).lower()
    if any(ext in texto_lower for ext in EXTENSIONES_DOCUMENTO):
        return 1
    if "[adjunto" in texto_lower and not any(ext in texto_lower for ext in EXTENSIONES_IMAGEN):
        return 1
    if any(p in texto_lower for p in PALABRAS_ARCHIVO) and not any(ext in texto_lower for ext in EXTENSIONES_IMAGEN):
        return 1
    return 0


def detectar_indicador_imagen(texto: str) -> int:
    """Menciones de imagen adjunta (jpg, png, gif) — técnica clásica de evasión de filtros de texto."""
    texto_lower = str(texto).lower()
    return int(any(ext in texto_lower for ext in EXTENSIONES_IMAGEN))


def detectar_indicador_asunto(asunto: str) -> int:
    """Asunto vacío, muy corto, todo en mayúsculas, o con símbolos repetidos (!!!, $$$)."""
    asunto = str(asunto).strip()
    if asunto == "" or asunto.lower() == "nan":
        return 1
    if len(asunto.split()) <= 1:
        return 1
    letras = [c for c in asunto if c.isalpha()]
    if letras and all(c.isupper() for c in letras):
        return 1
    if re.search(r"([!$%*]{2,})", asunto):
        return 1
    return 0


def calcular_indicadores(remitente: str, asunto: str, texto: str) -> dict:
    return {
        "correo": detectar_indicador_correo(remitente),
        "url": detectar_indicador_url(asunto, texto),
        "archivo": detectar_indicador_archivo(texto),
        "imagen": detectar_indicador_imagen(texto),
        "asunto": detectar_indicador_asunto(asunto),
    }
