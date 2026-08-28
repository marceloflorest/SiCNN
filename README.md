# Detector de Phishing — SiCNN + Blockchain

Este proyecto usa ÚNICAMENTE el algoritmo SiCNN (no AlexNet) para detectar
phishing en tu dataset de correos, y registra los resultados en una
blockchain (SHA-256), igual que el proyecto `phishing_detector` original.

## Cómo procesa el Excel
SiCNN es una CNN diseñada para imágenes, no texto. Por eso cada correo
(asunto + remitente + texto) se convierte primero en una "imagen" numérica
mediante hashing de palabras (ver `text_to_image.py`). Esto permite usar
la arquitectura real de SiCNN sobre tu dataset de texto, mientras no
tengas capturas de pantalla reales.

**Cuando tengas imágenes reales**: en `train.py` hay instrucciones para
reemplazar la conversión de texto por carga directa de imágenes — la
arquitectura de SiCNN no cambia, solo la fuente de datos.

## Estructura
```
sicnn_phishing_detector/
├── models.py                 # Arquitectura SiCNN
├── text_to_image.py          # Convierte texto de correo a imagen
├── train.py                  # Entrena SiCNN con tu Excel
├── analyze_excel.py          # Analiza el Excel completo, reporte txt
├── analyze_and_register.py   # Analiza + registra resultado en blockchain
├── blockchain.py             # Cadena SHA-256 (igual que phishing_detector)
└── requirements.txt
```

## Pasos en VS Code

### 1. Entorno virtual
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Entrena el modelo con tu Excel
```powershell
python train.py --input "C:\Users\marce\Downloads\dataset_hospital\phishing_dataset_hospital_es_2020_2025 (1).xlsx" --epochs 5
```
Esto genera `sicnn_final.keras`. Puede tardar varios minutos (convierte 5,300 correos a imágenes y entrena la CNN).

### 3. Analiza el Excel completo (reporte igual a phishing_detector)
```powershell
python analyze_excel.py --input "C:\Users\marce\Downloads\dataset_hospital\phishing_dataset_hospital_es_2020_2025 (1).xlsx" --mostrar-legitimos --guardar-txt reporte_sicnn.txt
```

### 4. Analiza y registra en blockchain en un solo paso
```powershell
python analyze_and_register.py --input "C:\Users\marce\Downloads\dataset_hospital\phishing_dataset_hospital_es_2020_2025 (1).xlsx" --guardar-txt reporte_sicnn.txt
```

## Formato del reporte (igual en ambos proyectos, SiCNN y SiCNN)
```
Algoritmo: SiCNN
Total de correos analizados: 5300
Legítimos: 5200
Phishing:  100

=== Correos marcados como PHISHING ===
- [98.3%] remitente@dominio.com | Asunto: ...

=== Correos marcados como LEGÍTIMOS (5200) ===
- [1.1%] remitente@essalud.gob.pe | Asunto: ...
```
