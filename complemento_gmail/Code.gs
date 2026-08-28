/**
 * COMPLEMENTO DE GMAIL - Detección de Phishing (SiCNN)
 * =========================================================
 * IMPORTANTE: cambia esta URL por la de tu servidor (ver instrucciones
 * en README_complemento.md sobre cómo exponerlo con ngrok).
 */
const URL_SERVIDOR = "http://127.0.0.1:5000"; // <-- CAMBIAR por tu URL de ngrok

/**
 * Se ejecuta cuando el usuario abre Gmail SIN tener un correo abierto
 * (ej. viendo la bandeja de entrada). Ofrece analizar varios correos.
 */
function alAbrirBandeja(e) {
  return construirTarjeta({
    contexto: "bandeja",
    tituloBoton: "Analizar bandeja de entrada",
    funcionAnalizar: "analizarBandeja",
  });
}

/**
 * Se ejecuta cuando el usuario tiene un correo ABIERTO. Ofrece analizar
 * solo ese correo.
 */
function alAbrirCorreo(e) {
  return construirTarjeta({
    contexto: "correo",
    tituloBoton: "Analizar este correo",
    funcionAnalizar: "analizarCorreoActual",
    messageId: e.gmail ? e.gmail.messageId : null,
  });
}

/**
 * Construye la tarjeta visual: botón de analizar, y botón de descargar
 * (bloqueado hasta que se haya analizado algo).
 */
function construirTarjeta(opciones) {
  const props = PropertiesService.getUserProperties();
  const tokenGuardado = props.getProperty("ultimo_token");
  const archivoGuardado = props.getProperty("ultimo_archivo");

  const seccionAnalizar = CardService.newCardSection()
    .setHeader("Detección de correo");

  const botonAnalizar = CardService.newTextButton()
    .setText(opciones.tituloBoton)
    .setOnClickAction(
      CardService.newAction()
        .setFunctionName(opciones.funcionAnalizar)
        .setParameters(opciones.messageId ? { messageId: opciones.messageId } : {})
    );
  seccionAnalizar.addWidget(botonAnalizar);

  const botonDescargar = CardService.newTextButton().setText("Descargar informe (Excel)");

  if (tokenGuardado && archivoGuardado) {
    // Habilitado: abre el enlace de descarga en el navegador
    botonDescargar.setOpenLink(
      CardService.newOpenLink().setUrl(`${URL_SERVIDOR}/descargar/${archivoGuardado}`)
    );
  } else {
    // Bloqueado: sin analizar aún, el botón no hace nada
    botonDescargar.setDisabled(true);
  }
  seccionAnalizar.addWidget(botonDescargar);

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Detección de Phishing"))
    .addSection(seccionAnalizar);

  return card.build();
}

/**
 * Analiza los correos recientes de la bandeja de entrada.
 */
function analizarBandeja(e) {
  const hilos = GmailApp.getInboxThreads(0, 15); // últimos 15 hilos
  const correos = [];

  hilos.forEach((hilo) => {
    const mensajes = hilo.getMessages();
    const ultimo = mensajes[mensajes.length - 1];
    correos.push({
      id: ultimo.getId(),
      fecha_hora: Utilities.formatDate(ultimo.getDate(), Session.getScriptTimeZone(), "dd/MM/yyyy HH:mm"),
      asunto: ultimo.getSubject() || "",
      remitente: ultimo.getFrom() || "",
      texto_correo: ultimo.getPlainBody().substring(0, 3000), // límite razonable
    });
  });

  return enviarYMostrarResultado(correos, "bandeja");
}

/**
 * Analiza solo el correo actualmente abierto.
 */
function analizarCorreoActual(e) {
  const messageId = e.parameters.messageId;
  const mensaje = GmailApp.getMessageById(messageId);

  const correo = {
    id: mensaje.getId(),
    fecha_hora: Utilities.formatDate(mensaje.getDate(), Session.getScriptTimeZone(), "dd/MM/yyyy HH:mm"),
    asunto: mensaje.getSubject() || "",
    remitente: mensaje.getFrom() || "",
    texto_correo: mensaje.getPlainBody().substring(0, 3000),
  };

  return enviarYMostrarResultado([correo], "correo");
}

/**
 * Envía los correos extraídos al servidor Python para clasificar, y
 * construye la tarjeta de resultado.
 */
function enviarYMostrarResultado(correos, contexto) {
  const opciones = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ correos: correos }),
    muteHttpExceptions: true,
  };

  const respuesta = UrlFetchApp.fetch(`${URL_SERVIDOR}/api/analizar`, opciones);
  const datos = JSON.parse(respuesta.getContentText());

  if (datos.error) {
    return construirTarjetaError(datos.error);
  }

  // Guardar el token/archivo para habilitar el botón de descarga
  const props = PropertiesService.getUserProperties();
  props.setProperty("ultimo_token", datos.token);
  props.setProperty("ultimo_archivo", datos.archivo);

  return construirTarjetaResultado(datos, contexto);
}

function construirTarjetaResultado(datos, contexto) {
  const seccion = CardService.newCardSection().setHeader("Resultado del análisis");

  seccion.addWidget(
    CardService.newKeyValue()
      .setTopLabel("Total analizado")
      .setContent(String(datos.total))
  );
  seccion.addWidget(
    CardService.newKeyValue()
      .setTopLabel("Legítimos")
      .setContent(String(datos.legitimos))
  );
  seccion.addWidget(
    CardService.newKeyValue()
      .setTopLabel("Phishing")
      .setContent(String(datos.phishing))
  );

  // Si es un solo correo, mostrar el detalle directo
  if (contexto === "correo" && datos.resultados.length === 1) {
    const r = datos.resultados[0];
    seccion.addWidget(
      CardService.newKeyValue()
        .setTopLabel("Clasificación")
        .setContent(`${r.clasificacion} (${r.probabilidad_phishing}%)`)
    );
  }

  if (datos.blockchain) {
    seccion.addWidget(
      CardService.newKeyValue()
        .setTopLabel("Registrado en Blockchain")
        .setContent(`${datos.blockchain.bloques_creados} bloque(s) — ${datos.blockchain.cadena_valida ? "Cadena válida ✓" : "⚠ Cadena corrompida"}`)
    );
  }

  const botonDescargar = CardService.newTextButton()
    .setText("Descargar informe (Excel)")
    .setOpenLink(CardService.newOpenLink().setUrl(`${URL_SERVIDOR}/descargar/${datos.archivo}`));
  seccion.addWidget(botonDescargar);

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Detección de Phishing"))
    .addSection(seccion);

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().updateCard(card.build()))
    .build();
}

function construirTarjetaError(mensajeError) {
  const seccion = CardService.newCardSection().setHeader("Error");
  seccion.addWidget(CardService.newTextParagraph().setText(mensajeError));

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Detección de Phishing"))
    .addSection(seccion);

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().updateCard(card.build()))
    .build();
}
