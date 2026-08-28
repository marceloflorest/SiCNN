# Complemento de Gmail — Detección de Phishing

Este complemento agrega un ícono en la barra lateral derecha de Gmail.
Al hacer clic, aparece un panel con:
- Un botón para **analizar** (bandeja completa, o solo el correo abierto)
- Un botón para **descargar el informe en Excel** (bloqueado hasta que analices algo)

## Requisito: tu servidor debe estar accesible desde internet

Los servidores de Google (donde corre el complemento) no pueden ver tu
`127.0.0.1:5000` — eso solo existe dentro de tu computadora. Necesitamos
exponerlo temporalmente con **ngrok** (gratuito).

### Paso 1: Instalar ngrok
1. Ve a https://ngrok.com/download y descarga la versión para Windows
2. Descomprime el .zip, obtendrás `ngrok.exe`
3. Crea una cuenta gratuita en ngrok.com, y sigue las instrucciones para
   conectar tu cuenta (`ngrok config add-authtoken TU_TOKEN`)

### Paso 2: Correr tu servidor Python (como siempre)
En una terminal de VS Code:
```powershell
python web_app.py
```
Déjalo corriendo.

### Paso 3: Exponerlo con ngrok
En OTRA terminal (fuera de VS Code, o una segunda pestaña):
```powershell
ngrok http 5000
```
Esto te va a dar una URL pública como:
```
https://a1b2-c3d4-e5f6.ngrok-free.app
```
**Cópiala** — la vas a necesitar en el siguiente paso. Debes dejar esta
ventana de ngrok abierta mientras uses el complemento (si la cierras, la
URL deja de funcionar y tendrás que generar una nueva).

## Paso 4: Crear el proyecto de Google Apps Script
1. Ve a https://script.google.com/
2. Clic en **"Proyecto nuevo"**
3. Borra el contenido de `Code.gs` que aparece por defecto, y pega el
   contenido del archivo `Code.gs` de esta carpeta
4. En la línea `const URL_SERVIDOR = "http://127.0.0.1:5000";`, reemplaza
   la URL por la que te dio ngrok (sin `/` al final), ej:
   ```javascript
   const URL_SERVIDOR = "https://a1b2-c3d4-e5f6.ngrok-free.app";
   ```
5. En el menú izquierdo, clic en el ícono de engranaje ⚙️ ("Configuración
   del proyecto") → marca **"Mostrar archivo de manifiesto 'appsscript.json'
   en el editor"**
6. Vuelve al editor, abre `appsscript.json`, borra su contenido y pega el
   contenido del archivo `appsscript.json` de esta carpeta
7. En ese archivo, dentro de `"openLinkUrlPrefixes"`, reemplaza también
   la URL de ngrok por la tuya

## Paso 5: Publicar el complemento (solo para ti, modo de prueba)
1. En Apps Script, arriba a la derecha, clic en **"Implementar"** →
   **"Probar implementaciones"**
2. Selecciona **"Instalar el complemento"**
3. Acepta los permisos que te pida (lectura de Gmail, etc.)

## Paso 6: Usarlo en Gmail
1. Abre (o recarga) **gmail.com**
2. En la barra lateral derecha, deberías ver un nuevo ícono (el de tu
   complemento)
3. Haz clic en él:
   - Si estás viendo la bandeja de entrada → botón "Analizar bandeja de entrada"
   - Si tienes un correo abierto → botón "Analizar este correo"
4. Tras analizar, el botón "Descargar informe (Excel)" se activa
5. Al hacer clic, se abre una pestaña nueva del navegador y descarga el
   Excel a tu carpeta de Descargas

---

## Notas importantes
- Mientras pruebas, deja abiertas **3 cosas** a la vez: tu servidor Python
  (`python web_app.py`), ngrok (`ngrok http 5000`), y Gmail
- Cada vez que reinicies ngrok sin una cuenta paga, la URL cambia — vas a
  tener que actualizarla en `Code.gs` y `appsscript.json` cada vez
- Este complemento solo lo puedes usar tú (modo de prueba/desarrollador),
  no está publicado públicamente — perfecto para tu demostración de tesis
