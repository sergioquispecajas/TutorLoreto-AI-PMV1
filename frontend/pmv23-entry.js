/* TutorLoreto AI - PMV2 + PMV3: perfil, práctica, evaluación e historial. */
'use strict';

VISTAS.add('aprendizaje-perfil');
VISTAS.add('aprendizaje-practica');
VISTAS.add('aprendizaje-resolver');
VISTAS.add('aprendizaje-resultado');
VISTAS.add('aprendizaje-historial');
VISTAS.add('aprendizaje-progreso');

const aprendizaje = {
  perfil: null,
  practica: null,
  iniciadoEn: null,
  pendienteExplicacion: false,
  cargando: false
};
const perfilGuardado = sessionStorage.getItem('tutorloreto_perfil');
if (perfilGuardado) aprendizaje.identificador = perfilGuardado;

function textoSeguro(valor) {
  return String(valor ?? '');
}
function nodo(tag, clase, contenido) {
  const el = document.createElement(tag);
  if (clase) el.className = clase;
  if (contenido !== undefined) el.textContent = textoSeguro(contenido);
  return el;
}
function alertaAprendizaje(elemento, mensaje, error = false) {
  elemento.textContent = mensaje;
  elemento.classList.toggle('mensaje-error', error);
}
function irAprendizaje(vista) {
  if (!VISTAS.has(vista)) return;
  ir(vista);
  if (vista === 'aprendizaje-perfil') prepararPerfil();
  if (vista === 'aprendizaje-practica') cargarSelectorPractica();
  if (vista === 'aprendizaje-historial') cargarHistorial();
  if (vista === 'aprendizaje-progreso') cargarProgreso();
}

function insertarVistasAprendizaje() {
  const main = document.querySelector('#contenido');
  if (!main || document.getElementById('vista-aprendizaje-perfil')) return;
  main.insertAdjacentHTML('beforeend', `
    <section class="vista pmv-view" id="vista-aprendizaje-perfil" data-vista="aprendizaje-perfil" hidden aria-labelledby="pmv-titulo-perfil">
      <header class="cabecera cabecera-simple"><button type="button" class="flecha-volver" data-pmv-back="inicio" aria-label="Volver">←</button><div><span class="eyebrow">PMV2 · PERSONALIZACIÓN</span><h1 id="pmv-titulo-perfil">Mi perfil académico</h1></div></header>
      <div class="contenido-pantalla">
        <p class="texto-ayuda">Crea un identificador sencillo para guardar tus prácticas y consultar tu avance. No ingreses tu nombre completo, DNI, correo ni contraseña.</p>
        <form id="pmv-form-perfil" class="pmv-form">
          <label for="pmv-identificador">Identificador personal</label>
          <input id="pmv-identificador" name="identificador" minlength="3" maxlength="64" pattern="[A-Za-z0-9_-]+" placeholder="Ej.: estudiante_01" autocomplete="off" required>
          <small>Usa letras, números, guion o guion bajo. Recuérdalo para recuperar tu historial.</small>
          <label for="pmv-grado">Grado de secundaria</label>
          <select id="pmv-grado" name="grado" required><option value="">Selecciona tu grado</option><option value="1">1.º de secundaria</option><option value="2">2.º de secundaria</option><option value="3">3.º de secundaria</option><option value="4">4.º de secundaria</option><option value="5">5.º de secundaria</option></select>
          <label for="pmv-nivel">¿Cómo describirías tu nivel académico actual?</label>
          <select id="pmv-nivel" name="nivel_academico" required><option value="">Selecciona una opción</option><option value="basico">Necesito explicaciones sencillas y más ejemplos</option><option value="intermedio">Comprendo algunos temas y practico para mejorar</option><option value="avanzado">Comprendo los conceptos y busco retos adicionales</option></select>
          <button class="btn btn-primario btn-ancho" type="submit">Guardar mi perfil →</button>
        </form>
        <p id="pmv-perfil-mensaje" role="status" aria-live="polite" class="pmv-mensaje"></p>
        <div class="nota-local"><span aria-hidden="true">🔒</span><span>El identificador es una referencia local del proyecto. No reemplaza un sistema de autenticación si la aplicación se despliega a varios usuarios en producción.</span></div>
      </div>
    </section>

    <section class="vista pmv-view" id="vista-aprendizaje-practica" data-vista="aprendizaje-practica" hidden aria-labelledby="pmv-titulo-practica">
      <header class="cabecera cabecera-simple"><button type="button" class="flecha-volver" data-pmv-back="inicio" aria-label="Volver">←</button><div><span class="eyebrow">PMV2 · HU12–HU14</span><h1 id="pmv-titulo-practica">Práctica personalizada</h1></div></header>
      <div class="contenido-pantalla">
        <div class="pmv-profile-chip" id="pmv-perfil-resumen">Perfil no seleccionado</div>
        <p class="texto-ayuda">Elige tu asignatura, escribe el tema que deseas practicar y selecciona la dificultad. La dificultad adaptativa considera tu perfil y resultados anteriores.</p>
        <form id="pmv-form-practica" class="pmv-form">
          <label for="pmv-asignatura">Asignatura</label><select id="pmv-asignatura" required><option value="">Cargando asignaturas…</option></select>
          <label for="pmv-tema">Tema de estudio</label><input id="pmv-tema" maxlength="160" minlength="2" placeholder="Ej.: fracciones, ecosistemas, comprensión lectora" required>
          <label for="pmv-dificultad">Nivel de dificultad</label><select id="pmv-dificultad"><option value="adaptativa">Adaptativa (recomendada)</option><option value="inicial">Inicial</option><option value="intermedia">Intermedia</option><option value="avanzada">Avanzada</option></select>
          <label for="pmv-cantidad">Cantidad de ejercicios</label><select id="pmv-cantidad"><option value="5">5 ejercicios</option><option value="7">7 ejercicios</option><option value="10">10 ejercicios</option></select>
          <button class="btn btn-primario btn-ancho" type="submit">Generar mis ejercicios con IA →</button>
        </form>
        <p id="pmv-practica-mensaje" role="status" aria-live="polite" class="pmv-mensaje"></p>
        <div class="nota-local"><span aria-hidden="true">🧠</span><span>Los ejercicios se generan con Ollama instalado en el servidor. Comprueba el contenido y la respuesta con tu material de clase; la IA puede cometer errores.</span></div>
      </div>
    </section>

    <section class="vista pmv-view" id="vista-aprendizaje-resolver" data-vista="aprendizaje-resolver" hidden aria-labelledby="pmv-titulo-resolver">
      <header class="cabecera cabecera-simple"><button type="button" class="flecha-volver" data-pmv-back="aprendizaje-practica" aria-label="Volver">←</button><div><span class="eyebrow">PMV2 · RESOLUCIÓN</span><h1 id="pmv-titulo-resolver">Resuelve la práctica</h1></div></header>
      <div class="contenido-pantalla">
        <div id="pmv-practica-meta" class="pmv-profile-chip"></div>
        <form id="pmv-form-resolver"><div id="pmv-ejercicios"></div><button class="btn btn-primario btn-ancho" type="submit">Enviar respuestas y ver resultados →</button></form>
        <p id="pmv-resolver-mensaje" role="status" aria-live="polite" class="pmv-mensaje"></p>
      </div>
    </section>

    <section class="vista pmv-view" id="vista-aprendizaje-resultado" data-vista="aprendizaje-resultado" hidden aria-labelledby="pmv-titulo-resultado">
      <header class="cabecera cabecera-simple"><button type="button" class="flecha-volver" data-pmv-back="aprendizaje-practica" aria-label="Volver">←</button><div><span class="eyebrow">PMV2 · RETROALIMENTACIÓN</span><h1 id="pmv-titulo-resultado">Resultado de tu práctica</h1></div></header>
      <div class="contenido-pantalla">
        <div class="pmv-score"><strong id="pmv-score-numero">—</strong><span id="pmv-score-texto">Tu resultado</span></div>
        <div id="pmv-resultado-detalle"></div>
        <button class="btn btn-primario btn-ancho" type="button" data-pmv-open="aprendizaje-progreso">Ver mi progreso →</button>
        <button class="btn btn-secundario btn-ancho" type="button" data-pmv-open="aprendizaje-practica">Practicar otro tema</button>
      </div>
    </section>

    <section class="vista pmv-view" id="vista-aprendizaje-historial" data-vista="aprendizaje-historial" hidden aria-labelledby="pmv-titulo-historial">
      <header class="cabecera cabecera-simple"><button type="button" class="flecha-volver" data-pmv-back="inicio" aria-label="Volver">←</button><div><span class="eyebrow">PMV3 · HU18</span><h1 id="pmv-titulo-historial">Mi historial</h1></div></header>
      <div class="contenido-pantalla">
        <p class="texto-ayuda">Aquí puedes consultar las prácticas que has realizado con este perfil.</p>
        <div id="pmv-historial-lista" class="pmv-lista" aria-live="polite"></div>
        <p id="pmv-historial-mensaje" class="pmv-mensaje" role="status"></p>
        <button class="btn btn-secundario btn-ancho" type="button" id="pmv-historial-actualizar">Actualizar historial</button>
      </div>
    </section>

    <section class="vista pmv-view" id="vista-aprendizaje-progreso" data-vista="aprendizaje-progreso" hidden aria-labelledby="pmv-titulo-progreso">
      <header class="cabecera cabecera-simple"><button type="button" class="flecha-volver" data-pmv-back="inicio" aria-label="Volver">←</button><div><span class="eyebrow">PMV3 · HU19–HU20</span><h1 id="pmv-titulo-progreso">Mi progreso académico</h1></div></header>
      <div class="contenido-pantalla">
        <div class="pmv-metricas">
          <article><strong id="pmv-total-practicas">0</strong><span>Prácticas</span></article>
          <article><strong id="pmv-total-preguntas">0</strong><span>Respuestas</span></article>
          <article><strong id="pmv-porcentaje-global">0%</strong><span>Aciertos</span></article>
        </div>
        <h2 class="pmv-subtitulo">Progreso por asignatura</h2><div id="pmv-progreso-asignaturas"></div>
        <h2 class="pmv-subtitulo">Desempeño por tema</h2><div id="pmv-progreso-temas"></div>
        <h2 class="pmv-subtitulo">Recomendaciones de IA</h2>
        <button class="btn btn-primario btn-ancho" type="button" id="pmv-analizar-recomendaciones">Analizar mi historial →</button>
        <p id="pmv-recomendacion-mensaje" class="pmv-mensaje" role="status" aria-live="polite"></p>
        <div id="pmv-recomendaciones" class="pmv-lista"></div>
        <p class="texto-ayuda">Las recomendaciones son orientativas, se calculan con las prácticas registradas y no constituyen una calificación oficial ni sustituyen al docente.</p>
      </div>
    </section>
  `);

  const menu = document.querySelector('#vista-inicio .accesos-grid');
  if (menu) {
    menu.insertAdjacentHTML('beforeend', `
      <button type="button" class="acceso acceso-lila" data-pmv-open="aprendizaje-perfil"><span class="acceso-emoji">👤</span><strong>Mi perfil</strong><small>Personaliza el tutor</small></button>
      <button type="button" class="acceso acceso-verde" data-pmv-open="aprendizaje-practica"><span class="acceso-emoji">📝</span><strong>Practicar</strong><small>Ejercicios adaptativos</small></button>
      <button type="button" class="acceso acceso-azul" data-pmv-open="aprendizaje-historial"><span class="acceso-emoji">🕘</span><strong>Historial</strong><small>Mis actividades</small></button>
      <button type="button" class="acceso acceso-rosa" data-pmv-open="aprendizaje-progreso"><span class="acceso-emoji">📈</span><strong>Mi progreso</strong><small>Avance y refuerzo</small></button>`);
  }

  const registro = document.querySelector('#vista-registro .contenido-pantalla');
  if (registro) {
    const boton = nodo('button', 'btn btn-secundario btn-ancho', 'Explicación adaptada a mi nivel →');
    boton.type = 'button';
    boton.id = 'pmv-explicacion-adaptada';
    registro.insertBefore(boton, $('otra-consulta-registro'));
    boton.addEventListener('click', solicitarExplicacionAdaptada);
  }
}

insertarVistasAprendizaje();

function pedirPerfil() {
  if (!aprendizaje.perfil) {
    irAprendizaje('aprendizaje-perfil');
    return false;
  }
  return true;
}

function prepararPerfil() {
  const input = $('pmv-identificador');
  if (aprendizaje.identificador) input.value = aprendizaje.identificador;
  if (aprendizaje.perfil) {
    $('pmv-grado').value = String(aprendizaje.perfil.grado);
    $('pmv-nivel').value = aprendizaje.perfil.nivel_academico;
    $('pmv-perfil-resumen').textContent = 'Perfil: ' + aprendizaje.perfil.grado + '.º · ' + aprendizaje.perfil.nivel_academico;
  }
}
$('pmv-form-perfil').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const boton = evento.currentTarget.querySelector('button[type="submit"]');
  const mensaje = $('pmv-perfil-mensaje');
  boton.disabled = true;
  alertaAprendizaje(mensaje, 'Guardando el perfil…');
  try {
    const perfil = await pedir('/api/aprendizaje/perfil', {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        identificador: $('pmv-identificador').value.trim(),
        grado: Number($('pmv-grado').value),
        nivel_academico: $('pmv-nivel').value
      })
    });
    aprendizaje.perfil = perfil;
    aprendizaje.identificador = perfil.identificador;
    sessionStorage.setItem('tutorloreto_perfil', perfil.identificador);
    alertaAprendizaje(mensaje, 'Perfil guardado correctamente.');
    if (aprendizaje.pendienteExplicacion) {
      aprendizaje.pendienteExplicacion = false;
      await generarExplicacionAdaptada();
    } else {
      irAprendizaje('aprendizaje-practica');
    }
  } catch (error) {
    alertaAprendizaje(mensaje, error.mensaje || 'No se pudo guardar el perfil.', true);
  } finally {
    boton.disabled = false;
  }
});

async function recuperarPerfil() {
  if (!aprendizaje.identificador) return;
  try {
    aprendizaje.perfil = await pedir('/api/aprendizaje/perfil/' + encodeURIComponent(aprendizaje.identificador));
  } catch {
    aprendizaje.perfil = null;
    sessionStorage.removeItem('tutorloreto_perfil');
  }
}

async function cargarSelectorPractica() {
  if (!pedirPerfil()) return;
  $('pmv-perfil-resumen').textContent =
    'Perfil: ' + aprendizaje.perfil.grado + '.º de secundaria · ' +
    aprendizaje.perfil.nivel_academico;
  const select = $('pmv-asignatura');
  select.replaceChildren(nodo('option', '', 'Cargando asignaturas…'));
  try {
    const asignaturas = await pedir('/api/asignaturas');
    select.replaceChildren(nodo('option', '', 'Selecciona una asignatura'));
    select.options[0].value = '';
    asignaturas.forEach(item => {
      const option = nodo('option', '', item.nombre);
      option.value = String(item.id);
      select.append(option);
    });
  } catch (error) {
    select.replaceChildren(nodo('option', '', 'No se pudo cargar el catálogo'));
    alertaAprendizaje($('pmv-practica-mensaje'), error.mensaje || 'No se pudo cargar las asignaturas.', true);
  }
}

$('pmv-form-practica').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  if (!pedirPerfil()) return;
  const boton = evento.currentTarget.querySelector('button[type="submit"]');
  const mensaje = $('pmv-practica-mensaje');
  boton.disabled = true;
  alertaAprendizaje(mensaje, 'Generando ejercicios con la IA local…');
  try {
    const practica = await pedir('/api/aprendizaje/practicas', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        identificador: aprendizaje.perfil.identificador,
        asignatura_id: Number($('pmv-asignatura').value),
        tema: $('pmv-tema').value.trim(),
        dificultad: $('pmv-dificultad').value,
        cantidad: Number($('pmv-cantidad').value)
      })
    });
    aprendizaje.practica = practica;
    aprendizaje.iniciadoEn = Date.now();
    pintarEjercicios(practica);
    irAprendizaje('aprendizaje-resolver');
  } catch (error) {
    alertaAprendizaje(mensaje, error.mensaje || 'No se pudo generar la práctica. Comprueba Ollama.', true);
  } finally {
    boton.disabled = false;
  }
});

function pintarEjercicios(practica) {
  $('pmv-practica-meta').textContent =
    practica.asignatura + ' · ' + practica.tema + ' · Dificultad ' + practica.dificultad;
  const caja = $('pmv-ejercicios');
  caja.replaceChildren();
  practica.ejercicios.forEach((ejercicio, indice) => {
    const articulo = nodo('article', 'pmv-ejercicio');
    const titulo = nodo('h3', '', 'Pregunta ' + (indice + 1) + ' de ' + practica.ejercicios.length);
    const pregunta = nodo('p', 'pmv-enunciado', ejercicio.enunciado);
    articulo.append(titulo, pregunta);
    const grupo = nodo('fieldset', 'pmv-opciones');
    const leyenda = nodo('legend', '', 'Selecciona una alternativa');
    grupo.append(leyenda);
    ['A', 'B', 'C', 'D'].forEach(letra => {
      const label = nodo('label', 'pmv-opcion');
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = 'ejercicio-' + ejercicio.id;
      input.value = letra;
      input.required = true;
      const texto = nodo('span', '', letra + '. ' + ejercicio.opciones[letra]);
      label.append(input, texto);
      grupo.append(label);
    });
    articulo.append(grupo);
    caja.append(articulo);
  });
  $('pmv-resolver-mensaje').textContent = '';
}

$('pmv-form-resolver').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  if (!aprendizaje.practica || !aprendizaje.perfil) return;
  const boton = evento.currentTarget.querySelector('button[type="submit"]');
  const respuestas = [];
  for (const ejercicio of aprendizaje.practica.ejercicios) {
    const seleccionado = document.querySelector('input[name="ejercicio-' + ejercicio.id + '"]:checked');
    if (!seleccionado) {
      alertaAprendizaje($('pmv-resolver-mensaje'), 'Responde todas las preguntas antes de finalizar.', true);
      return;
    }
    respuestas.push({ejercicio_id: ejercicio.id, respuesta: seleccionado.value});
  }
  boton.disabled = true;
  alertaAprendizaje($('pmv-resolver-mensaje'), 'Evaluando tus respuestas…');
  try {
    const duracion = Math.max(0, Math.round((Date.now() - aprendizaje.iniciadoEn) / 1000));
    const resultado = await pedir('/api/aprendizaje/practicas/' +
      aprendizaje.practica.id + '/respuestas', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        identificador: aprendizaje.perfil.identificador,
        respuestas,
        duracion_segundos: duracion
      })
    });
    aprendizaje.practica = resultado;
    pintarResultado(resultado);
    irAprendizaje('aprendizaje-resultado');
  } catch (error) {
    alertaAprendizaje($('pmv-resolver-mensaje'), error.mensaje || 'No se pudo guardar la evaluación.', true);
  } finally {
    boton.disabled = false;
  }
});

function pintarResultado(practica) {
  $('pmv-score-numero').textContent = practica.porcentaje_aciertos + '%';
  $('pmv-score-texto').textContent = practica.aciertos + ' aciertos de ' + practica.total_ejercicios;
  const caja = $('pmv-resultado-detalle');
  caja.replaceChildren();
  practica.ejercicios.forEach(ejercicio => {
    const articulo = nodo('article', 'pmv-feedback ' + (ejercicio.es_correcta ? 'correcto' : 'incorrecto'));
    articulo.append(
      nodo('h3', '', 'Pregunta ' + ejercicio.numero + ' · ' + (ejercicio.es_correcta ? '¡Correcto!' : 'Puedes mejorar')),
      nodo('p', '', ejercicio.enunciado),
      nodo('p', 'pmv-feedback-respuesta', 'Tu respuesta: ' + (ejercicio.respuesta || '—') +
        ' · Respuesta correcta: ' + ejercicio.respuesta_correcta),
      nodo('p', 'pmv-feedback-explicacion', ejercicio.explicacion)
    );
    caja.append(articulo);
  });
}

function tarjetaActividad(item) {
  const articulo = nodo('article', 'pmv-lista-item');
  articulo.append(
    nodo('strong', '', item.asignatura + ' · ' + item.tema),
    nodo('span', '', item.dificultad + ' · ' + item.estado),
    nodo('p', '', item.porcentaje_aciertos === null ?
      'Práctica pendiente de finalizar' :
      item.aciertos + ' de ' + item.total_ejercicios + ' aciertos · ' + item.porcentaje_aciertos + '%'),
    nodo('small', '', 'Creada: ' + new Date(item.creado_en).toLocaleString('es-PE'))
  );
  return articulo;
}

async function cargarHistorial() {
  if (!pedirPerfil()) return;
  const caja = $('pmv-historial-lista');
  caja.replaceChildren(nodo('p', 'texto-ayuda', 'Cargando historial…'));
  try {
    const datos = await pedir('/api/aprendizaje/historial/' +
      encodeURIComponent(aprendizaje.perfil.identificador));
    caja.replaceChildren();
    if (!datos.actividades.length) {
      caja.append(nodo('p', 'texto-ayuda', 'Aún no tienes actividades registradas. Completa tu primera práctica.'));
      return;
    }
    datos.actividades.forEach(item => caja.append(tarjetaActividad(item)));
  } catch (error) {
    alertaAprendizaje($('pmv-historial-mensaje'), error.mensaje || 'No se pudo cargar el historial.', true);
  }
}

function barraProgreso(nombre, porcentaje, detalle) {
  const caja = nodo('article', 'pmv-barra-item');
  const cabecera = nodo('div', 'pmv-barra-cabecera');
  cabecera.append(nodo('strong', '', nombre), nodo('span', '', porcentaje + '%'));
  const fondo = nodo('div', 'pmv-barra-fondo');
  const avance = nodo('div', 'pmv-barra-avance');
  avance.style.width = Math.max(0, Math.min(100, porcentaje)) + '%';
  fondo.append(avance);
  caja.append(cabecera, fondo, nodo('small', '', detalle));
  return caja;
}

async function cargarProgreso() {
  if (!pedirPerfil()) return;
  try {
    const datos = await pedir('/api/aprendizaje/progreso/' +
      encodeURIComponent(aprendizaje.perfil.identificador));
    $('pmv-total-practicas').textContent = datos.total_practicas;
    $('pmv-total-preguntas').textContent = datos.total_preguntas;
    $('pmv-porcentaje-global').textContent = datos.porcentaje_global + '%';
    const asignaturas = $('pmv-progreso-asignaturas');
    asignaturas.replaceChildren();
    if (!datos.asignaturas.length) asignaturas.append(nodo('p', 'texto-ayuda', 'Completa prácticas para visualizar el progreso.'));
    datos.asignaturas.forEach(item => asignaturas.append(
      barraProgreso(item.asignatura, item.porcentaje_aciertos,
        item.aciertos + ' aciertos de ' + item.respuestas + ' respuestas · ' + item.sesiones + ' prácticas')
    ));
    const temas = $('pmv-progreso-temas');
    temas.replaceChildren();
    if (!datos.temas.length) temas.append(nodo('p', 'texto-ayuda', 'Todavía no hay resultados por tema.'));
    datos.temas.forEach(item => temas.append(
      barraProgreso(item.asignatura + ' · ' + item.tema, item.porcentaje_aciertos,
        item.aciertos + ' aciertos de ' + item.respuestas + ' respuestas')
    ));
    $('pmv-recomendaciones').replaceChildren();
    $('pmv-recomendacion-mensaje').textContent = '';
  } catch (error) {
    alertaAprendizaje($('pmv-recomendacion-mensaje'), error.mensaje || 'No se pudo calcular el progreso.', true);
  }
}

$('pmv-analizar-recomendaciones').addEventListener('click', async (evento) => {
  if (!pedirPerfil()) return;
  const boton = evento.currentTarget;
  boton.disabled = true;
  const mensaje = $('pmv-recomendacion-mensaje');
  alertaAprendizaje(mensaje, 'Analizando tus resultados con la IA local…');
  const caja = $('pmv-recomendaciones');
  caja.replaceChildren();
  try {
    const datos = await pedir('/api/aprendizaje/recomendaciones/' +
      encodeURIComponent(aprendizaje.perfil.identificador));
    alertaAprendizaje(mensaje, datos.resumen || 'Análisis completado.');
    if (!datos.temas_prioritarios.length) {
      caja.append(nodo('p', 'texto-ayuda', datos.requiere_datos ?
        'Completa una práctica para recibir recomendaciones basadas en tu desempeño.' :
        'No se identificaron temas prioritarios en los datos disponibles.'));
    }
    datos.temas_prioritarios.forEach(item => {
      const tarjeta = nodo('article', 'pmv-lista-item');
      tarjeta.append(
        nodo('strong', '', item.asignatura + ' · ' + item.tema),
        nodo('p', '', item.razon),
        nodo('p', 'pmv-feedback-explicacion', item.accion)
      );
      caja.append(tarjeta);
    });
  } catch (error) {
    alertaAprendizaje(mensaje, error.mensaje || 'No fue posible analizar el historial. Comprueba Ollama.', true);
  } finally {
    boton.disabled = false;
  }
});

$('pmv-historial-actualizar').addEventListener('click', cargarHistorial);

async function generarExplicacionAdaptada() {
  if (!aprendizaje.perfil) {
    aprendizaje.pendienteExplicacion = true;
    irAprendizaje('aprendizaje-perfil');
    return;
  }
  if (!state.consultaId) {
    decir('Registra primero una consulta para adaptarla a tu perfil.');
    return;
  }
  if (aprendizaje.cargando) return;
  aprendizaje.cargando = true;
  ir('procesando');
  try {
    const respuesta = await pedir('/api/aprendizaje/explicaciones/' +
      encodeURIComponent(state.consultaId), {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({identificador: aprendizaje.perfil.identificador})
    });
    state.respuesta = respuesta;
    poner('curso-explicacion', nombreActual());
    poner('pregunta-explicacion', state.pregunta);
    mostrarExplicacion(respuesta.contenido);
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(document.getElementById('explicacion-pasos'), {
        delimiters: [
          {left:'$$', right:'$$', display:true},
          {left:'\\[', right:'\\]', display:true},
          {left:'\\(', right:'\\)', display:false}
        ],
        throwOnError: false
      });
    }
    ir('explicacion');
  } catch (error) {
    poner('detalle-error-ia', error.mensaje || 'No fue posible generar la explicación adaptada.');
    ir('error_ia');
  } finally {
    aprendizaje.cargando = false;
  }
}
function solicitarExplicacionAdaptada() {
  generarExplicacionAdaptada();
}

document.addEventListener('click', evento => {
  const abrir = evento.target.closest('[data-pmv-open]');
  if (abrir) {
    evento.preventDefault();
    if (abrir.dataset.pmvOpen === 'aprendizaje-practica' ||
        abrir.dataset.pmvOpen === 'aprendizaje-historial' ||
        abrir.dataset.pmvOpen === 'aprendizaje-progreso') {
      if (!pedirPerfil()) return;
    }
    irAprendizaje(abrir.dataset.pmvOpen);
  }
  const volver = evento.target.closest('[data-pmv-back]');
  if (volver) {
    evento.preventDefault();
    irAprendizaje(volver.dataset.pmvBack);
  }
});

if (aprendizaje.identificador) {
  recuperarPerfil().then(() => {
    if (aprendizaje.perfil) {
      const input = $('pmv-identificador');
      if (input) input.value = aprendizaje.perfil.identificador;
    }
  });
}
