/**
 * COMPLEMENTO DE GMAIL - Detección de Phishing (AlexNet)
 */
const URL_SERVIDOR = "https://cash-politely-detector.ngrok-free.dev"; // URL de tu servidor ngrok

/**
 * Se ejecuta al abrir Gmail sin correo seleccionado (Bandeja de entrada).
 * IMPORTANTE: Debe devolver un ARREGLO de tarjetas: [ tarjeta ]
 */
function alAbrirBandeja(e) {
  return [
    construirTarjeta({
      contexto: "bandeja",
      tituloBoton: "Analizar bandeja de entrada",
      funcionAnalizar: "analizarBandeja",
    })
  ];
}

/**
 * Se ejecuta al abrir un correo electrónico específico.
 * IMPORTANTE: Debe devolver un ARREGLO de tarjetas: [ tarjeta ]
 */
function alAbrirCorreo(e) {
  const messageId = (e && e.gmail && e.gmail.messageId) ? e.gmail.messageId : null;
  return [
    construirTarjeta({
      contexto: "correo",
      tituloBoton: "Analizar este correo",
      funcionAnalizar: "analizarCorreoActual",
      messageId: messageId,
    })
  ];
}

/**
 * Construye la interfaz visual inicial.
 */
function construirTarjeta(opciones) {
  const props = PropertiesService.getUserProperties();
  const tokenGuardado = props.getProperty("ultimo_token");
  const archivoGuardado = props.getProperty("ultimo_archivo");

  const seccionAnalizar = CardService.newCardSection()
    .setHeader("Detección de correo");

  const accionAnalizar = CardService.newAction()
    .setFunctionName(opciones.funcionAnalizar);
  
  if (opciones.messageId) {
    accionAnalizar.setParameters({ messageId: String(opciones.messageId) });
  }

  const botonAnalizar = CardService.newTextButton()
    .setText(opciones.tituloBoton)
    .setOnClickAction(accionAnalizar);

  seccionAnalizar.addWidget(botonAnalizar);

  if (tokenGuardado && archivoGuardado) {
    const botonDescargar = CardService.newTextButton()
      .setText("Descargar último informe (Excel)")
      .setOpenLink(
        CardService.newOpenLink().setUrl(`${URL_SERVIDOR}/descargar/${archivoGuardado}`)
      );
    seccionAnalizar.addWidget(botonDescargar);
  } else {
    seccionAnalizar.addWidget(
      CardService.newTextParagraph().setText("<i>Analiza correos para habilitar la descarga del informe Excel.</i>")
    );
  }

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Detección de Phishing"))
    .addSection(seccionAnalizar);

  return card.build();
}

/**
 * Analiza los correos recientes de la bandeja de entrada.
 */
function analizarBandeja(e) {
  const hilos = GmailApp.getInboxThreads(0, 15);
  const correos = [];

  hilos.forEach((hilo) => {
    const mensajes = hilo.getMessages();
    const ultimo = mensajes[mensajes.length - 1];
    correos.push({
      id: ultimo.getId(),
      fecha_hora: Utilities.formatDate(ultimo.getDate(), Session.getScriptTimeZone(), "dd/MM/yyyy HH:mm"),
      asunto: ultimo.getSubject() || "",
      remitente: ultimo.getFrom() || "",
      texto_correo: ultimo.getPlainBody().substring(0, 3000),
    });
  });

  return enviarYMostrarResultado(correos, "bandeja");
}

/**
 * Analiza solo el correo actual.
 */
function analizarCorreoActual(e) {
  const messageId = e.parameters ? e.parameters.messageId : null;
  
  if (!messageId) {
    return construirTarjetaError("No se pudo obtener el ID del correo actual.");
  }

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
 * Envía los datos a tu backend Flask/FastAPI en Ngrok.
 */
function enviarYMostrarResultado(correos, contexto) {
  const opciones = {
    method: "post",
    contentType: "application/json",
    headers: {
      "ngrok-skip-browser-warning": "true" 
    },
    payload: JSON.stringify({ correos: correos }),
    muteHttpExceptions: true,
  };

  try {
    const respuesta = UrlFetchApp.fetch(`${URL_SERVIDOR}/api/analizar`, opciones);
    const contenido = respuesta.getContentText();
    const datos = JSON.parse(contenido);

    if (datos.error) {
      return construirTarjetaError(datos.error);
    }

    const props = PropertiesService.getUserProperties();
    props.setProperty("ultimo_token", datos.token || "");
    props.setProperty("ultimo_archivo", datos.archivo || "");

    return construirTarjetaResultado(datos, contexto);
  } catch (err) {
    return construirTarjetaError("Error al conectar con el servidor ngrok: " + err.message);
  }
}

/**
 * Renderiza los resultados procesados en la tarjeta.
 */
function construirTarjetaResultado(datos, contexto) {
  const seccion = CardService.newCardSection().setHeader("Resultado del análisis");

  seccion.addWidget(
    CardService.newDecoratedText()
      .setTopLabel("Total analizado")
      .setText(String(datos.total))
  );
  seccion.addWidget(
    CardService.newDecoratedText()
      .setTopLabel("Legítimos")
      .setText(String(datos.legitimos))
  );
  seccion.addWidget(
    CardService.newDecoratedText()
      .setTopLabel("Phishing")
      .setText(String(datos.phishing))
  );

  if (contexto === "correo" && datos.resultados && datos.resultados.length === 1) {
    const r = datos.resultados[0];
    seccion.addWidget(
      CardService.newDecoratedText()
        .setTopLabel("Clasificación")
        .setText(`${r.clasificacion} (${r.probabilidad_phishing}%)`)
    );
  }

  if (datos.blockchain) {
    seccion.addWidget(
      CardService.newDecoratedText()
        .setTopLabel("Registrado en Blockchain")
        .setText(`${datos.blockchain.bloques_creados} bloque(s) — ${datos.blockchain.cadena_valida ? "Cadena válida ✓" : "⚠ Cadena corrompida"}`)
    );
  }

  if (datos.archivo) {
    const botonDescargar = CardService.newTextButton()
      .setText("Descargar informe (Excel)")
      .setOpenLink(CardService.newOpenLink().setUrl(`${URL_SERVIDOR}/descargar/${datos.archivo}`));
    seccion.addWidget(botonDescargar);
  }

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Detección de Phishing"))
    .addSection(seccion);

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().updateCard(card.build()))
    .build();
}

/**
 * Renderiza mensajes de error.
 */
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
